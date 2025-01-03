import argparse
import os
from src import create_app

def parse_arguments():
    parser = argparse.ArgumentParser(description='ACOS Prometheus Exporter')
    parser.add_argument('-c', '--config', type=str, default='config.yml', help='Path to the configuration file')
    parser.add_argument('-l', '--log', type=str, default='INFO', help='Log level, this will override the log level in the config file')
    parser.add_argument('-e', '--env', type=str, default='development', help='Environment: development or production')
    parser.add_argument('-p', '--metric_prefix', type=str, default='acos', help='Prefix for the metrics')
    return parser.parse_args()

def main():
    args = parse_arguments()
    os.environ['LOG_LEVEL'] = args.log
    os.environ['CONFIG_FILE'] = args.config
    os.environ['METRIC_PREFIX'] = args.metric_prefix
    print(f"Starting exporter with config file: {args.config}, log level: {args.log}, and metric prefix: {args.metric_prefix}")
    app = create_app(args.env)
    app.run(debug=app.config['DEBUG'], port=9734, host='0.0.0.0')

if __name__ == '__main__':
    main()
