'''
File:   serial_command_generator.py

Spec:   Open a serial port and send hand typed commands through it.
        Used to send test commands to serial_command_handler.py.
        * Not to be used in real deployments! * 

Usage:  python3 test_scripts/serial_command_generator.py
'''

import os
import pty
import select
import termios
import time

def disable_pty_echo(fd):
    """Disable echo and canonical mode on the slave PTY so master doesn't read its own writes."""
    attrs = termios.tcgetattr(fd)
    # Clear ECHO (echo input chars) and ICANON (canonical mode)
    attrs[3] = attrs[3] & ~termios.ECHO & ~termios.ICANON
    termios.tcsetattr(fd, termios.TCSANOW, attrs)

def main():
    # 1. Create a pseudo-terminal pair (built-in Python module)
    master, slave = pty.openpty()
    
    # Disable echoing on the slave device
    disable_pty_echo(slave)

    slave_port_name = os.ttyname(slave)

    print("=" * 60)
    print("Virtual Serial Port Created!")
    print(f"Set your handler script's SERIAL_PORT to: {slave_port_name}")
    print("=" * 60)
    print("Type your commands below (or 'exit' to quit):\n")

    try:
        while True:
            try:
                cmd = input("Send command > ")
            except EOFError:
                break

            if cmd.strip() == "exit": 
                break

            # Write data to the master end; your listener reads from slave_port_name
            payload = (cmd + "\n").encode("utf-8")
            os.write(master, payload)
            print(f" -> Sent: {repr(payload)}")

            # Give the handler script a moment to process and start sending bytes
            time.sleep(0.05)

            # Drain loop: continuously collect chunks until the port goes quiet
            response_bytes = b""
            while True:
                # Check for available data with a 0.2-second quiet timeout
                rlist, _, _ = select.select([master], [], [], 0.2)
                if master in rlist:
                    try:
                        chunk = os.read(master, 4096)
                        if not chunk:
                            break
                        response_bytes += chunk
                    except OSError:
                        # Handles slave disconnects gracefully
                        break
                else:
                    # No more data arriving within 200ms window
                    break

            # Print accumulated response
            if response_bytes:
                print("\n<- Received the following response:")
                print(f"{repr(response_bytes.decode('utf-8', errors='ignore'))}")

    except KeyboardInterrupt:
        print("\nClosing port.")
    finally:
        os.close(master)
        os.close(slave)

if __name__ == "__main__":
    main()