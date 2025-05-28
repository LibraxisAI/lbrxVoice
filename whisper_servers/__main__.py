"""
Main entry point for the whisper_servers package.
"""
import argparse
import sys
import os

from whisper_servers.common.logging import logger


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="MLX Whisper Servers")
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Batch server command
    batch_parser = subparsers.add_parser("batch", help="Run the batch transcription server")
    batch_parser.add_argument("--port", type=int, help="Port to run the server on (default: 8123)")
    batch_parser.add_argument("--model", type=str, help="Model to use (default: large-v3)")
    
    # Realtime server command
    realtime_parser = subparsers.add_parser("realtime", help="Run the realtime transcription server")
    realtime_parser.add_argument("--port", type=int, help="Port to run the server on (default: 8000)")
    realtime_parser.add_argument("--model", type=str, help="Model to use (default: tiny)")
    
    # Version command
    version_parser = subparsers.add_parser("version", help="Show version information")
    
    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_args()
    
    if args.command == "batch":
        # Set environment variables if provided
        if args.port:
            os.environ["BATCH_PORT"] = str(args.port)
        if args.model:
            os.environ["BATCH_MODEL"] = args.model
            
        # Import and run batch server
        from whisper_servers.scripts.run_batch import main as run_batch
        run_batch()
    
    elif args.command == "realtime":
        # Set environment variables if provided
        if args.port:
            os.environ["REALTIME_PORT"] = str(args.port)
        if args.model:
            os.environ["REALTIME_MODEL"] = args.model
            
        # Import and run realtime server
        from whisper_servers.scripts.run_realtime import main as run_realtime
        run_realtime()
    
    elif args.command == "version":
        print("MLX Whisper Servers v0.1.0")
    
    else:
        # Show help if no command is provided
        print("Please specify a command: batch, realtime, or version")
        sys.exit(1)


if __name__ == "__main__":
    main()
