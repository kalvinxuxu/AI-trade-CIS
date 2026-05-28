import argparse
import sys

# Import step functions
from data.fetchers.stock_list_fetcher import sync_stock_list
from data.fetchers.daily_bar_fetcher import fetch_daily_for_date, fetch_latest_daily


def main():
    parser = argparse.ArgumentParser(description="CIS Research Agent Worker")
    parser.add_argument("--step", type=str, required=True,
                        choices=["sync_stock_list", "fetch_daily", "fetch_sector", "fetch_index",
                                "calc_all_indicators", "detect_events", "generate_report", "all"])
    parser.add_argument("--date", type=str, help="Trade date (YYYY-MM-DD)")

    args = parser.parse_args()
    print(f"Running step: {args.step}, date: {args.date}")

    # Execute the selected step
    if args.step == "sync_stock_list":
        success = sync_stock_list()
    elif args.step == "fetch_daily":
        if args.date:
            success = fetch_daily_for_date(args.date)
        else:
            success = fetch_latest_daily()
    elif args.step == "all":
        # Run all steps in sequence
        print("Running all steps...")
        success = sync_stock_list()
        if success and args.date:
            success = fetch_daily_for_date(args.date)
        elif success:
            success = fetch_latest_daily()
    else:
        print(f"Step {args.step} not yet implemented")
        success = False

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()