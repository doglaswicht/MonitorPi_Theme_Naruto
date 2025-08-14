#!/usr/bin/env python3
"""Ponto de entrada principal do painel de dispositivos de rede."""

from panel import NetworkPanel


def main():
    """Função principal."""
    panel = NetworkPanel()
    panel.run()


if __name__ == "__main__":
    main()
