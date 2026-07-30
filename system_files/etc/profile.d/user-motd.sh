# Konsole / interactive-shell welcome banner.
# Replaces Bazzite's tip markdown with Arcalium fastfetch (ASCII logo + specs).
# Toggle off per-user with:  touch ~/.config/no-show-user-motd
# (ujust toggle-user-motd still works — it manages that same file.)
if [ -z "$USERMOTDSOURCED" ]; then
  USERMOTDSOURCED="Y"
  if test -d "$HOME"; then
    if test ! -e "$HOME"/.config/no-show-user-motd; then
      if test -x /usr/bin/fastfetch; then
        /usr/bin/fastfetch -c /usr/share/arcalium/fastfetch.jsonc
      elif test -x /usr/libexec/ublue-motd; then
        /usr/libexec/ublue-motd
      fi
    fi
  fi
fi
