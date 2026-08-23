# Konsole / interactive-shell welcome banner.
# Arcalium logo + short specs + command tips (not Bazzite tip markdown).
# Toggle off per-user with:  touch ~/.config/no-show-user-motd
# (ujust toggle-user-motd still works — it manages that same file.)
if [ -z "$USERMOTDSOURCED" ]; then
  USERMOTDSOURCED="Y"
  if test -d "$HOME"; then
    if test ! -e "$HOME"/.config/no-show-user-motd; then
      if test -x /usr/libexec/arcalium-motd; then
        /usr/libexec/arcalium-motd
      elif test -x /usr/bin/fastfetch; then
        /usr/bin/fastfetch -c /usr/share/arcalium/fastfetch.jsonc
      elif test -x /usr/libexec/ublue-motd; then
        /usr/libexec/ublue-motd
      fi
    fi
  fi
fi
