# Arcalium Konsole / fish welcome banner (same as bash profile.d/user-motd.sh).
if status is-interactive
    if not set -q USERMOTDSOURCED
        set -gx USERMOTDSOURCED Y
        if test -d "$HOME"; and not test -e "$HOME/.config/no-show-user-motd"
            if test -x /usr/libexec/arcalium-motd
                /usr/libexec/arcalium-motd
            end
        end
    end
end
