"""TTS Servers main entry point"""

import argparse
import sys


def main():
    parser = argparse.ArgumentParser(description="TTS Servers")
    parser.add_argument(
        "server",
        choices=["dia-ws", "dia-rest", "csm-rest"],
        help="Server to run"
    )
    
    args = parser.parse_args()
    
    if args.server == "dia-ws":
        from .dia.websocket_server import main as dia_ws_main
        dia_ws_main()
    elif args.server == "dia-rest":
        from .dia.rest_api import main as dia_rest_main
        dia_rest_main()
    elif args.server == "csm-rest":
        from .csm.rest_api import main as csm_rest_main
        csm_rest_main()
    else:
        print(f"Unknown server: {args.server}")
        sys.exit(1)


if __name__ == "__main__":
    main()