# Arcalium overrides Bazzite's fastfetch/neofetch aliases so Konsole and
# manual `fastfetch` / `neofetch` calls show our logo and image metadata.
# Real /usr/bin/neofetch + neowofetch wrappers also exist for non-alias callers.
alias neofetch='/usr/bin/fastfetch -c /usr/share/arcalium/fastfetch.jsonc'
alias neowofetch='/usr/bin/fastfetch -c /usr/share/arcalium/fastfetch.jsonc'
alias fastfetch='/usr/bin/fastfetch -c /usr/share/arcalium/fastfetch.jsonc'
