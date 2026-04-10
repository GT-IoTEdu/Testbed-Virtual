#!/bin/bash
sudo ip link add bridge-tap type bridge
sudo ip link set bridge-tap up
sudo ip tuntap add dev tap0 mode tap
sudo ip link set tap0 master bridge-tap
sudo ip link set tap0 up


docker build ./target-server  -t servidor_alvo:latest




docker build ./teste_ataque -t atacante:latest
