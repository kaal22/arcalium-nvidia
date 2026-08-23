# Safety net: always try Arcalium MOTD last if nothing else showed it.
# Filename zz-* sorts after bazzite-neofetch / user-motd.
case $- in
  *i*) ;;
  *) return 0 ;;
esac

if [ -n "${ARCALIUM_MOTD_DONE:-}" ]; then
  return 0
fi
if [ ! -d "${HOME:-}" ] || [ -e "${HOME}/.config/no-show-user-motd" ]; then
  return 0
fi
if [ -x /usr/libexec/arcalium-motd ]; then
  /usr/libexec/arcalium-motd
  ARCALIUM_MOTD_DONE=1
  export ARCALIUM_MOTD_DONE
fi
