#!/usr/bin/env python3
"""Ponto de entrada principal do painel de dispositivos de rede."""

from panel import NetworkPanel


def main():
    """Função principal."""
    try:
        panel = NetworkPanel()
        panel.run()
    except KeyboardInterrupt:
        print("\n🛑 Painel encerrado pelo usuário")
    except Exception as e:
        print(f"❌ Erro no painel: {e}")


if __name__ == "__main__":
    main()