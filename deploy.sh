#!/usr/bin/env bash
cat > gpu-board-server.service << EOF
[Unit]
Description=GPU Board Server
After=network.target

[Service]
ExecStart=