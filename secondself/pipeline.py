import argparse
import sys


def cmd_classify():
    from classify import run_classification
    print("=== Running Classifier ===")
    run_classification()


def cmd_link(threshold=None):
    from link import run_linking
    print("=== Running Auto-Linker ===")
    if threshold is not None:
        run_linking(threshold=threshold)
    else:
        run_linking()


def cmd_process(threshold=None):
    cmd_classify()
    print()
    cmd_link(threshold=threshold)
    print()
    from build_graph import build_graph
    print("=== Rebuilding Graph ===")
    build_graph()
    print()
    print("=== Pipeline Complete ===")


def main():
    parser = argparse.ArgumentParser(
        description="SecondSelf Pipeline Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  classify   Classify all unprocessed raw captures into wiki/
  link       Compute embeddings and auto-link related wiki notes
  process    Run classify + link in sequence (full pipeline)

Examples:
  python pipeline.py classify
  python pipeline.py link
  python pipeline.py link --threshold 0.80
  python pipeline.py process
        """
    )
    subparsers = parser.add_subparsers(dest="command")

    # classify
    subparsers.add_parser("classify", help="Classify raw captures into wiki/")

    # link
    link_parser = subparsers.add_parser("link", help="Auto-link related wiki notes via embeddings")
    link_parser.add_argument(
        "--threshold", type=float, default=None,
        help="Cosine similarity threshold (default: 0.75)"
    )

    # process
    process_parser = subparsers.add_parser("process", help="Run classify + link in sequence")
    process_parser.add_argument(
        "--threshold", type=float, default=None,
        help="Cosine similarity threshold for linking (default: 0.75)"
    )

    args = parser.parse_args()

    if args.command == "classify":
        cmd_classify()
    elif args.command == "link":
        cmd_link(threshold=args.threshold)
    elif args.command == "process":
        cmd_process(threshold=args.threshold)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
