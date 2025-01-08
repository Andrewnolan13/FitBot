import signal

from .browser import EdgeLauncherThread
from .export import FitbitDataDaemon
from .dash_app import app

def main():
    def signal_handler(sig, frame):
        print("\nYou pressed Ctrl+C! Shutting down gracefully...")
        try:
            # daemon.stop()  # Stop the FitbitDataDaemon
            1
        except Exception as e:
            print(f"Error while shutting down the server: {e}")
        finally:
            print("Exiting...")
            import os
            cmd = "taskkill /IM python.exe /F"
            os.system(cmd)
        exit(0)

    # Attach the signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)

    print("Starting FitbitDataDaemon...")
    print("Press Ctrl+C to stop the program.")

    daemon = FitbitDataDaemon()
    browser = EdgeLauncherThread()
    daemon.start() 
    browser.start()

    app.run_server(debug=False, use_reloader=False)


if __name__ == '__main__':
    print("Starting __main__.py")
    main()
