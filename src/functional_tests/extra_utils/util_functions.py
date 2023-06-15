from django.db import connections


def varnish_cache():
    # Mannually running varnish cache sim code
    cursor = connections["default"].cursor()
    cursor.execute('''
        BEGIN;

        --
        -- "cheating" version of the varnish_purge() function
        -- that can be used on a local installation that doesn't
        -- have any frontends.
        --

        CREATE OR REPLACE FUNCTION varnish_purge(url text)
        RETURNS void
        AS $$
        $$ LANGUAGE 'sql';

        CREATE OR REPLACE FUNCTION varnish_purge_expr(expr text)
        RETURNS void
        AS $$
        $$ LANGUAGE 'sql';

        CREATE OR REPLACE FUNCTION varnish_purge_xkey(key text)
        RETURNS void
        AS $$
        $$ LANGUAGE 'sql';

        COMMIT;''')
    cursor.close()
