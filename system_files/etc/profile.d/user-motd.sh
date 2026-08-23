# Konsole / interactive-shell welcome banner.
# Arcalium logo + short specs + command tips (not Bazzite tip markdown).
# Sourced from /etc/profile (login) and /etc/bashrc → profile.d (Konsole tabs).
# Toggle off per-user with:  touch ~/.config/no-show-user-motd
# (ujust toggle-user-motd still works — it manages that same file.)

# Interactive shells only (skip scp/sftp/scripts).
# Use =~ i (not case *i*) — chat/markdown often strips the asterisks from *i*).
[[ $- =~ i ]] || return 0

if [ -z "${USERMOTDSOURCED:-}" ]; then
  USERMOTDSOURCED="Y"
  export USERMOTDSOURCED
  if [ -d "${HOME:-}" ] && [ ! -e "${HOME}/.config/no-show-user-motd" ]; then
    if [ -x /usr/libexec/arcalium-motd ]; then
      /usr/libexec/arcalium-motd
      ARCALIUM_MOTD_DONE=1
      export ARCALIUM_MOTD_DONE
    elif [ -x /usr/bin/fastfetch ] && [ -f /usr/share/arcalium/fastfetch.jsonc ]; then
      /usr/bin/fastfetch -c /usr/share/arcalium/fastfetch.jsonc
      if [ -f /usr/share/arcalium/motd-tips.txt ]; then
        printf '\n'
        cat /usr/share/arcalium/motd-tips.txt
        printf '\n'
      fi
      ARCALIUM_MOTD_DONE=1
      export ARCALIUM_MOTD_DONE
    fi
  fi
fi
