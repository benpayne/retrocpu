#!/usr/bin/env python3
"""
RetroCPU Program Loader

Official tool for loading and executing programs on the RetroCPU via XMODEM.

Usage:
    load_program.py <binary_file> [options]

Options:
    -p, --port PORT      Serial port (default: /dev/ttyACM0)
    -b, --baud BAUD      Baud rate (default: 9600)
    -e, --execute        Execute the program after loading
    -v, --verbose        Verbose output

Examples:
    # Load a binary file
    load_program.py program.bin

    # Load and execute
    load_program.py program.bin --execute

    # Use different serial port
    load_program.py program.bin -p /dev/ttyUSB0 -e
"""

import serial
import time
import sys
import argparse


class XModemSender:
    """XMODEM protocol sender for RetroCPU"""

    SOH = 0x01
    EOT = 0x04
    ACK = 0x06
    NAK = 0x15

    def __init__(self, ser, verbose=False):
        self.ser = ser
        self.packet_num = 1
        self.verbose = verbose

    def calculate_checksum(self, data):
        """Calculate 8-bit checksum"""
        return sum(data) & 0xFF

    def send_packet(self, data):
        """Send a 128-byte XMODEM packet"""
        # Pad data to 128 bytes
        packet_data = data + b'\x00' * (128 - len(data))

        # Build packet: SOH + PKT# + ~PKT# + DATA[128] + CHECKSUM
        packet = bytes([
            self.SOH,
            self.packet_num & 0xFF,
            (~self.packet_num) & 0xFF
        ])
        packet += packet_data
        packet += bytes([self.calculate_checksum(packet_data)])

        if self.verbose:
            print(f"  Packet #{self.packet_num}: {len(packet)} bytes, checksum 0x{packet[-1]:02X}")

        # Send entire packet at once
        self.ser.write(packet)
        self.ser.flush()

        # Wait for receiver to process the packet
        # CPU needs time to read from FIFO, check checksum, and send response
        time.sleep(0.05)  # 50ms processing time

        # Wait for ACK/NAK
        response = self.ser.read(1)
        if len(response) == 0:
            if self.verbose:
                print("  ERROR: No response (timeout)")
            return False

        if response[0] == self.ACK:
            if self.verbose:
                print(f"  ACK received")
            self.packet_num += 1
            return True
        elif response[0] == self.NAK:
            if self.verbose:
                print(f"  NAK received (retry)")
            return False
        else:
            if self.verbose:
                print(f"  ERROR: Unexpected response: 0x{response[0]:02X}")
            return False

    def send_file(self, data, max_retries=10):
        """Send complete file via XMODEM"""
        print(f"Transferring {len(data)} bytes via XMODEM...")

        # Wait for initial NAK from receiver
        if self.verbose:
            print("Waiting for receiver NAK...")
        start_time = time.time()
        while True:
            if self.ser.in_waiting > 0:
                ch = self.ser.read(1)
                if ch[0] == self.NAK:
                    if self.verbose:
                        print("Received initial NAK, starting transfer")
                    break
                else:
                    if self.verbose:
                        print(f"Ignoring byte: 0x{ch[0]:02X}")

            if time.time() - start_time > 3:
                print("ERROR: Timeout waiting for receiver")
                return False

            time.sleep(0.001)  # Check every 1ms

        # Send data in 128-byte packets
        offset = 0
        packets_sent = 0
        total_packets = (len(data) + 127) // 128

        while offset < len(data):
            chunk = data[offset:offset+128]

            retries = 0
            while retries < max_retries:
                if self.send_packet(chunk):
                    offset += len(chunk)
                    packets_sent += 1
                    if not self.verbose:
                        # Show progress bar for non-verbose mode
                        percent = (packets_sent * 100) // total_packets
                        bar = '=' * (percent // 5)
                        print(f"\r[{bar:<20}] {percent}%", end='', flush=True)
                    break
                retries += 1
                if self.verbose:
                    print(f"  Retry {retries}/{max_retries}")

            if retries >= max_retries:
                print("\nERROR: Max retries exceeded")
                return False

        if not self.verbose:
            print()  # New line after progress bar

        # Send EOT
        if self.verbose:
            print("Sending EOT...")
        self.ser.write(bytes([self.EOT]))
        self.ser.flush()

        response = self.ser.read(1)
        if len(response) > 0 and response[0] == self.ACK:
            print("Transfer complete!")
            return True
        else:
            print("ERROR: No ACK for EOT")
            return False


def load_program(binary_path, port='/dev/ttyACM0', baud=9600, execute=False, verbose=False):
    """Load a binary program to RetroCPU and optionally execute it"""

    # Read binary file
    try:
        with open(binary_path, 'rb') as f:
            binary_data = f.read()
    except FileNotFoundError:
        print(f"ERROR: File not found: {binary_path}")
        return 1
    except IOError as e:
        print(f"ERROR: Cannot read file: {e}")
        return 1

    if len(binary_data) == 0:
        print("ERROR: File is empty")
        return 1

    print(f"Loaded {binary_path} ({len(binary_data)} bytes)")

    # Open serial port
    try:
        with serial.Serial(port, baud, timeout=2) as ser:
            # Wait for port to stabilize
            time.sleep(0.5)
            ser.reset_input_buffer()

            # Get a fresh prompt
            if verbose:
                print("Getting monitor prompt...")
            ser.write(b'\r')
            ser.flush()
            time.sleep(0.5)
            response = ser.read_all().decode('latin1', errors='ignore')

            if verbose:
                print(f"Response: {repr(response)}")

            if '> ' not in response:
                print("ERROR: Monitor not responding (no prompt)")
                return 1

            if verbose:
                print("Monitor is ready")

            # Send L command to start XMODEM receive
            if verbose:
                print("Sending 'L' command to monitor...")
            ser.write(b'L\r')
            ser.flush()

            # Transfer file via XMODEM
            xmodem = XModemSender(ser, verbose=verbose)
            success = xmodem.send_file(binary_data)

            if not success:
                print("ERROR: Transfer failed")
                return 1

            # Read completion message
            time.sleep(0.5)
            response = ser.read_all().decode('latin1', errors='ignore')
            if verbose and response:
                print(f"Monitor response: {response}")

            # Execute if requested
            if execute:
                print("Executing program at $0300...")
                ser.write(b'J\r')
                ser.flush()

                # Wait for execution to complete and read output
                time.sleep(0.5)
                response = ser.read_all().decode('latin1', errors='ignore')

                # Print execution output (everything between "Executing" and "Execution complete")
                if "Executing at $0300..." in response and "Execution complete" in response:
                    start = response.find("Executing at $0300...") + len("Executing at $0300...")
                    end = response.find("Execution complete")
                    output = response[start:end].strip()
                    if output:
                        print("\nProgram output:")
                        print(output)
                    print("\nProgram execution complete")
                else:
                    print(f"Execution response: {response}")

            return 0

    except serial.SerialException as e:
        print(f"ERROR: Cannot open {port}: {e}")
        return 2
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        return 1


def main():
    parser = argparse.ArgumentParser(
        description='Load and execute programs on RetroCPU via XMODEM',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s program.bin                    # Load only
  %(prog)s program.bin --execute          # Load and execute
  %(prog)s program.bin -p /dev/ttyUSB0 -e # Use different port
        """
    )

    parser.add_argument('binary_file', help='Binary file to load')
    parser.add_argument('-p', '--port', default='/dev/ttyACM0', help='Serial port (default: /dev/ttyACM0)')
    parser.add_argument('-b', '--baud', type=int, default=9600, help='Baud rate (default: 9600)')
    parser.add_argument('-e', '--execute', action='store_true', help='Execute program after loading')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')

    args = parser.parse_args()

    result = load_program(
        args.binary_file,
        port=args.port,
        baud=args.baud,
        execute=args.execute,
        verbose=args.verbose
    )

    sys.exit(result)


if __name__ == "__main__":
    main()
