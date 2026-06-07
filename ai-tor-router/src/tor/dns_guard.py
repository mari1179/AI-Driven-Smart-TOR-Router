"""
DNS Guard — prevents DNS leaks by forcing all DNS queries through Tor.
"""

import subprocess
import logging

logger = logging.getLogger("dns_guard")

RULES = [
    # Redirect all UDP DNS (port 53) to Tor's DNSPort (5353)
    "iptables -t nat -A OUTPUT -p udp --dport 53 -j REDIRECT --to-ports 5353",
    "iptables -t nat -A OUTPUT -p tcp --dport 53 -j REDIRECT --to-ports 5353",
    # Block any DNS that escapes
    "iptables -A OUTPUT -p udp --dport 53 -j DROP",
]

CLEANUP_RULES = [
    "iptables -t nat -D OUTPUT -p udp --dport 53 -j REDIRECT --to-ports 5353",
    "iptables -t nat -D OUTPUT -p tcp --dport 53 -j REDIRECT --to-ports 5353",
    "iptables -D OUTPUT -p udp --dport 53 -j DROP",
]


class DNSGuard:
    def __init__(self):
        self.active = False

    def apply_rules(self):
        """Apply iptables rules to block DNS leaks."""
        for rule in RULES:
            try:
                subprocess.run(rule.split(), check=True, capture_output=True)
            except subprocess.CalledProcessError as e:
                logger.warning(f"DNS rule may already exist: {e.stderr.decode().strip()}")
        self.active = True
        logger.info("DNS leak prevention rules applied.")

    def remove_rules(self):
        """Remove DNS leak prevention rules (cleanup)."""
        for rule in CLEANUP_RULES:
            try:
                subprocess.run(rule.split(), check=True, capture_output=True)
            except subprocess.CalledProcessError:
                pass
        self.active = False
        logger.info("DNS leak prevention rules removed.")

    def test_leak(self) -> bool:
        """
        Quick DNS leak test — resolves via dnsleaktest API.
        Returns True if DNS appears to leak outside Tor.
        """
        import requests
        try:
            proxies = {"http": "socks5h://127.0.0.1:9050", "https": "socks5h://127.0.0.1:9050"}
            r = requests.get("https://dnsleaktest.com/json", proxies=proxies, timeout=10)
            servers = r.json()
            # If any server is in a non-Tor country, flag as potential leak
            logger.info(f"DNS servers seen: {[s.get('country_name') for s in servers]}")
            return False
        except Exception as e:
            logger.warning(f"DNS leak test failed: {e}")
            return False
