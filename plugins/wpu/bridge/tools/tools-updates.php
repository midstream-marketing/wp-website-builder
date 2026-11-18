<?php
/**
 * Plugin and theme updates with checks before and after, and automatic rollback.
 *
 * For each item: copy its folder to private storage, update it through WordPress's own upgrader, load
 * the site's key pages again, and if a page that worked before is now broken, put the old folder back.
 * WordPress core updates are reported only.
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/** How many update backups to keep (they can be large). */
const WPU_BT_KEEP_BACKUPS = 10;

function wpu_bt_updates_load() {
	require_once ABSPATH . 'wp-admin/includes/file.php';
	require_once ABSPATH . 'wp-admin/includes/misc.php';
	require_once ABSPATH . 'wp-admin/includes/plugin.php';
	require_once ABSPATH . 'wp-admin/includes/theme.php';
	require_once ABSPATH . 'wp-admin/includes/update.php';
	require_once ABSPATH . 'wp-admin/includes/class-wp-upgrader.php';
	if ( ! function_exists( 'wp_update_plugins' ) ) {
		require_once ABSPATH . WPINC . '/update.php';
	}
}

/** Why updates cannot run here, or ''. */
function wpu_bt_updates_blocker() {
	if ( defined( 'DISALLOW_FILE_MODS' ) && DISALLOW_FILE_MODS ) {
		return 'This site sets DISALLOW_FILE_MODS, so plugins and themes cannot be updated from WordPress.';
	}
	if ( ! class_exists( 'ZipArchive' ) ) {
		return 'PHP\'s zip extension is missing, so the bridge cannot keep a backup before updating. Update from wp-admin, or ask the host to enable php-zip.';
	}
	wpu_bt_updates_load();
	if ( 'direct' !== get_filesystem_method( array(), WP_PLUGIN_DIR ) ) {
		return 'WordPress needs FTP details to write files on this host, so updates cannot run from the bridge. Update from wp-admin, or set FS_METHOD to direct if the host allows it.';
	}
	return '';
}

function wpu_bt_plugin_slug( $file ) {
	$d = dirname( $file );
	return '.' === $d ? basename( $file, '.php' ) : $d;
}

/** Plugin ids look like "folder/file.php" or "file.php"; theme ids are one folder name. Nothing else. */
function wpu_bt_valid_item_id( $type, $id ) {
	$id = (string) $id;
	if ( false !== strpos( $id, '..' ) || false !== strpos( $id, '\\' ) ) {
		return false;
	}
	return 'plugin' === $type
		? (bool) preg_match( '#^[A-Za-z0-9._-]+(/[A-Za-z0-9._-]+\.php)?$#', $id ) && '.php' === substr( $id, -4 )
		: (bool) preg_match( '#^[A-Za-z0-9._-]+$#', $id );
}

/** Root folder and target (folder, or single file) of a plugin or theme, or array( '', '' ). Not resolved: the target may be missing. */
function wpu_bt_item_target( $type, $id ) {
	if ( ! wpu_bt_valid_item_id( $type, $id ) ) {
		return array( '', '' );
	}
	if ( 'plugin' === $type ) {
		$root = wp_normalize_path( (string) realpath( WP_PLUGIN_DIR ) );
		$rel  = '.' === dirname( $id ) ? $id : dirname( $id );
	} else {
		$root = wp_normalize_path( (string) realpath( get_theme_root( $id ) ) );
		$rel  = $id;
	}
	return '' === $root ? array( '', '' ) : array( $root, $root . '/' . $rel );
}

/** Folder (or single file) of an installed plugin or theme, resolved and checked to be directly inside its root. */
function wpu_bt_item_path( $type, $id ) {
	list( $root, $target ) = wpu_bt_item_target( $type, $id );
	if ( '' === $root ) {
		return '';
	}
	$real = wp_normalize_path( (string) realpath( $target ) );
	return '' !== $real && dirname( $real ) === $root ? $real : '';
}

/** Zip a folder (or one file) into $zip, top entry named basename($src). Links are skipped. */
function wpu_bt_zip_item( $src, $zip ) {
	$z = new ZipArchive();
	if ( true !== $z->open( $zip, ZipArchive::CREATE | ZipArchive::OVERWRITE ) ) {
		return false;
	}
	$base = basename( $src );
	$ok   = true;
	if ( is_file( $src ) ) {
		$ok = $z->addFile( $src, $base );
	} else {
		$z->addEmptyDir( $base );
		$it = new RecursiveIteratorIterator( new RecursiveDirectoryIterator( $src, FilesystemIterator::SKIP_DOTS ), RecursiveIteratorIterator::SELF_FIRST );
		foreach ( $it as $f ) {
			if ( $f->isLink() ) {
				continue;
			}
			$rel = $base . '/' . str_replace( '\\', '/', substr( $f->getPathname(), strlen( $src ) + 1 ) );
			$ok  = ( $f->isDir() ? $z->addEmptyDir( $rel ) : $z->addFile( $f->getPathname(), $rel ) ) && $ok;
		}
	}
	return $z->close() && $ok;
}

/** Unpack a backup made by wpu_bt_zip_item into $root. Every entry must sit under $top. */
function wpu_bt_unzip_item( $zip, $root, $top ) {
	$z = new ZipArchive();
	if ( true !== $z->open( $zip ) ) {
		return false;
	}
	for ( $i = 0; $i < $z->numFiles; $i++ ) {
		$n = (string) $z->getNameIndex( $i );
		if ( '' === $n || '/' === $n[0] || false !== strpos( $n, '..' ) || false !== strpos( $n, '\\' ) || ( $n !== $top && 0 !== strpos( $n, $top . '/' ) ) ) {
			$z->close();
			return false;
		}
	}
	$ok = $z->extractTo( $root );
	$z->close();
	return $ok;
}

wpu_bt_define_tool( 'updates_check', array(
	'title'       => 'Check for updates',
	'description' => 'Plugins and themes with updates waiting, with their PHP and WordPress requirements, and whether a WordPress core update exists (reported only).',
	'cap'         => 'update_plugins',
	'group'       => 'updates',
	'props'       => array( 'refresh' => array( 'type' => 'boolean', 'description' => 'Ask WordPress.org again first (default true).' ) ),
	'run'         => function ( $a ) {
		global $wp_version;
		wpu_bt_updates_load();
		if ( wpu_bt_bool( $a, 'refresh', true ) ) {
			wp_clean_plugins_cache( false );
			wp_update_plugins();
			wp_update_themes();
			wp_version_check();
		}
		$up      = get_site_transient( 'update_plugins' );
		$plugins = array();
		$all     = get_plugins();
		foreach ( isset( $up->response ) ? (array) $up->response : array() as $file => $info ) {
			if ( ! isset( $all[ $file ] ) ) {
				continue;
			}
			$req_php   = isset( $info->requires_php ) ? (string) $info->requires_php : '';
			$req_wp    = isset( $info->requires ) ? (string) $info->requires : '';
			$plugins[] = array(
				'file'         => $file,
				'name'         => $all[ $file ]['Name'],
				'active'       => is_plugin_active( $file ),
				'current'      => $all[ $file ]['Version'],
				'new'          => isset( $info->new_version ) ? $info->new_version : '',
				'requires_php' => $req_php,
				'requires_wp'  => $req_wp,
				'tested_wp'    => isset( $info->tested ) ? (string) $info->tested : '',
				'compatible'   => ( '' === $req_php || version_compare( PHP_VERSION, $req_php, '>=' ) ) && ( '' === $req_wp || version_compare( $wp_version, $req_wp, '>=' ) ),
				'package'      => ! empty( $info->package ),
				'self'         => plugin_basename( WPU_BT_FILE ) === $file,
			);
		}
		$ut     = get_site_transient( 'update_themes' );
		$themes = array();
		foreach ( isset( $ut->response ) ? (array) $ut->response : array() as $slug => $info ) {
			$t        = wp_get_theme( $slug );
			$themes[] = array(
				'slug'    => $slug,
				'name'    => $t->exists() ? $t->get( 'Name' ) : $slug,
				'active'  => get_stylesheet() === $slug || get_template() === $slug,
				'current' => $t->exists() ? $t->get( 'Version' ) : '',
				'new'     => isset( $info['new_version'] ) ? $info['new_version'] : '',
				'package' => ! empty( $info['package'] ),
			);
		}
		$core   = get_site_transient( 'update_core' );
		$latest = null;
		if ( isset( $core->updates ) ) {
			foreach ( (array) $core->updates as $u ) {
				if ( isset( $u->response ) && 'upgrade' === $u->response ) {
					$latest = $u->current;
					break;
				}
			}
		}
		return array(
			'plugins'      => $plugins,
			'themes'       => $themes,
			'core'         => array( 'current' => $wp_version, 'update' => $latest, 'note' => 'Core updates are not applied by the bridge.' ),
			'last_checked' => isset( $up->last_checked ) ? gmdate( 'c', (int) $up->last_checked ) : null,
			'blocked'      => wpu_bt_updates_blocker(),
		);
	},
) );

wpu_bt_define_tool( 'updates_apply', array(
	'title'       => 'Update plugins and themes',
	'description' => 'Update up to 5 plugins (by file, e.g. "akismet/akismet.php", or folder name) and themes (by folder). dry_run (the default) only shows the plan and runs the "before" check. '
		. 'When applied, each item is backed up, updated, then the key pages are loaded again; if a page that worked before now fails, the old version is put back automatically. '
		. 'Each successful update returns a change_id that change_undo uses to go back to the previous version.',
	'cap'         => 'update_plugins',
	'group'       => 'updates',
	'props'       => array(
		'plugins'              => array( 'type' => 'array', 'items' => array( 'type' => 'string' ) ),
		'themes'               => array( 'type' => 'array', 'items' => array( 'type' => 'string' ) ),
		'dry_run'              => array( 'type' => 'boolean', 'description' => 'Default true.' ),
		'check_urls'           => array( 'type' => 'array', 'items' => array( 'type' => 'string' ), 'description' => 'Pages to check before and after (up to 10 on this site). Default: home, newest post and page, shop and cart.' ),
		'stop_on_failure'      => array( 'type' => 'boolean', 'description' => 'Default true: stop after the first rollback.' ),
		'allow_without_checks' => array( 'type' => 'boolean', 'description' => 'Only when the site cannot load its own pages (the check reports a connection error). Updates then run without the safety check.' ),
	),
	'write'       => true,
	'destructive' => true,
	'run'         => function ( $a ) {
		$block = wpu_bt_updates_blocker();
		if ( '' !== $block ) {
			return wpu_bt_err( $block );
		}
		$plugins = isset( $a['plugins'] ) ? array_map( 'strval', (array) $a['plugins'] ) : array();
		$themes  = isset( $a['themes'] ) ? array_map( 'strval', (array) $a['themes'] ) : array();
		if ( ! $plugins && ! $themes ) {
			return wpu_bt_err( 'Name the plugins or themes to update (see updates_check).' );
		}
		if ( count( $plugins ) + count( $themes ) > 5 ) {
			return wpu_bt_err( 'At most 5 updates per call. Split the list.' );
		}
		if ( $themes && ! current_user_can( 'update_themes' ) ) {
			return wpu_bt_err( 'You cannot update themes.' );
		}

		// Resolve and validate every item before touching anything.
		$up    = get_site_transient( 'update_plugins' );
		$ut    = get_site_transient( 'update_themes' );
		$all   = get_plugins();
		$items = array();
		foreach ( $plugins as $p ) {
			$file = isset( $all[ $p ] ) ? $p : '';
			if ( '' === $file ) {
				foreach ( array_keys( $all ) as $f ) {
					if ( wpu_bt_plugin_slug( $f ) === $p ) {
						$file = $f;
						break;
					}
				}
			}
			if ( '' === $file ) {
				return wpu_bt_err( 'Plugin not installed: ' . $p );
			}
			if ( plugin_basename( WPU_BT_FILE ) === $file ) {
				return wpu_bt_err( 'WPU Bridge cannot update itself. Update it from Plugins in wp-admin.' );
			}
			if ( empty( $up->response[ $file ]->package ) ) {
				return wpu_bt_err( 'No update package is available for ' . $file . ' (run updates_check; premium plugins may need their licence active).' );
			}
			$items[] = array( 'type' => 'plugin', 'id' => $file, 'name' => $all[ $file ]['Name'], 'from' => $all[ $file ]['Version'], 'to' => $up->response[ $file ]->new_version, 'active' => is_plugin_active( $file ) );
		}
		foreach ( $themes as $t ) {
			$t = sanitize_key( $t ) === strtolower( $t ) ? $t : '';
			$theme = '' !== $t ? wp_get_theme( $t ) : null;
			if ( ! $theme || ! $theme->exists() ) {
				return wpu_bt_err( 'Theme not installed: ' . $t );
			}
			if ( empty( $ut->response[ $t ]['package'] ) ) {
				return wpu_bt_err( 'No update package is available for theme ' . $t . '.' );
			}
			$items[] = array( 'type' => 'theme', 'id' => $t, 'name' => $theme->get( 'Name' ), 'from' => $theme->get( 'Version' ), 'to' => $ut->response[ $t ]['new_version'], 'active' => get_stylesheet() === $t || get_template() === $t );
		}
		foreach ( $items as $it ) {
			if ( '' === wpu_bt_item_path( $it['type'], $it['id'] ) ) {
				return wpu_bt_err( 'Could not find the folder of ' . $it['name'] . '.' );
			}
		}

		$urls = ! empty( $a['check_urls'] ) ? array_slice( array_map( 'strval', (array) $a['check_urls'] ), 0, 10 ) : wpu_bt_default_check_urls();
		foreach ( $urls as $u ) {
			if ( ! wpu_bt_is_own_url( $u ) ) {
				return wpu_bt_err( 'Check pages must be on this site: ' . $u );
			}
		}
		$before    = wpu_bt_health( $urls );
		$reachable = array_filter( $before, function ( $r ) {
			return ! empty( $r['status'] );
		} );
		$checks_on = (bool) $reachable;
		$plan      = array();
		foreach ( $items as $it ) {
			$plan[] = array( 'type' => $it['type'], 'id' => $it['id'], 'name' => $it['name'], 'from' => $it['from'], 'to' => $it['to'], 'active' => $it['active'] );
		}
		if ( wpu_bt_bool( $a, 'dry_run', true ) ) {
			return array(
				'dry_run'         => true,
				'plan'            => $plan,
				'before'          => $before,
				'already_broken'  => array_values( array_filter( $before, function ( $r ) {
					return empty( $r['ok'] );
				} ) ),
				'checks_possible' => $checks_on,
				'next'            => 'Call again with dry_run false to apply.',
			);
		}
		if ( ! $checks_on && ! wpu_bt_bool( $a, 'allow_without_checks' ) ) {
			return wpu_bt_err( 'The site could not load its own pages, so the before/after safety check cannot run. Nothing was updated. Pass allow_without_checks true only if you accept updating without it.' );
		}

		$results = array();
		$stop    = wpu_bt_bool( $a, 'stop_on_failure', true );
		foreach ( $items as $it ) {
			$r         = wpu_bt_update_one( $it, $urls, $before, $checks_on );
			$results[] = $r;
			if ( $stop && in_array( $r['status'], array( 'rolled_back', 'failed', 'rollback_failed' ), true ) ) {
				break;
			}
		}
		wpu_bt_prune_backups();
		return array(
			'dry_run' => false,
			'results' => $results,
			'after'   => $checks_on ? wpu_bt_health( $urls ) : array(),
			'not_run' => array_values( array_slice( $plan, count( $results ) ) ),
		);
	},
) );

/** Update one item with backup, check and rollback. */
function wpu_bt_update_one( array $it, array $urls, array $before, $checks_on ) {
	$out  = array( 'type' => $it['type'], 'id' => $it['id'], 'name' => $it['name'], 'from' => $it['from'], 'to' => $it['to'] );
	$path = wpu_bt_item_path( $it['type'], $it['id'] );
	$cid  = wpu_bt_new_change_id();
	$base = wpu_bt_private_dir( 'updates' );
	if ( '' === $base ) {
		return $out + array( 'status' => 'failed', 'error' => 'No private folder for the backup, so nothing was updated.' );
	}
	$backup = $base . '/' . $cid . '/' . basename( $path ) . '.zip';
	if ( ! wpu_bt_prepare_dir( dirname( $backup ) ) || ! wpu_bt_zip_item( $path, $backup ) ) {
		wpu_bt_rrmdir( $base . '/' . $cid );
		return $out + array( 'status' => 'failed', 'error' => 'The backup copy failed (disk full?), so nothing was updated.' );
	}

	$skin = new WP_Ajax_Upgrader_Skin();
	if ( 'plugin' === $it['type'] ) {
		$upgrader = new Plugin_Upgrader( $skin );
		$res      = $upgrader->bulk_upgrade( array( $it['id'] ) );
	} else {
		$upgrader = new Theme_Upgrader( $skin );
		$res      = $upgrader->bulk_upgrade( array( $it['id'] ) );
	}
	$one    = is_array( $res ) && isset( $res[ $it['id'] ] ) ? $res[ $it['id'] ] : $res;
	$errors = $skin->get_errors();
	$failed = ! $one || is_wp_error( $one ) || ( $errors instanceof WP_Error && $errors->has_errors() );

	if ( ! $failed && 'plugin' === $it['type'] ) {
		wp_clean_plugins_cache();
		if ( $it['active'] && ! is_plugin_active( $it['id'] ) ) {
			$act = activate_plugin( $it['id'], '', false, true );
			if ( is_wp_error( $act ) ) {
				$failed = true;
				$errors = $act;
			}
		}
	}
	if ( 'theme' === $it['type'] ) {
		wp_clean_themes_cache();
	}

	$after       = $checks_on ? wpu_bt_health( $urls ) : array();
	$regressions = $checks_on ? wpu_bt_health_regressions( $before, $after ) : array();
	if ( ! $failed && ! $regressions ) {
		$now = 'plugin' === $it['type'] ? get_plugin_data( WP_PLUGIN_DIR . '/' . $it['id'], false, false )['Version'] : wp_get_theme( $it['id'] )->get( 'Version' );
		wpu_bt_change_add( 'updates_apply', 'Updated ' . $it['name'] . ' ' . $it['from'] . ' -> ' . $now, array(
			'kind'   => 'files',
			'type'   => $it['type'],
			'id'     => $it['id'],
			'name'   => $it['name'],
			'from'   => $it['from'],
			'active' => $it['active'],
			'backup' => $backup,
		), $cid );
		return $out + array( 'status' => 'updated', 'now' => $now, 'checks' => $checks_on ? 'all pages that worked before still work' : 'not run', 'change_id' => $cid );
	}

	// Put the old version back.
	$why = $failed ? ( is_wp_error( $one ) ? $one->get_error_message() : ( $errors instanceof WP_Error && $errors->has_errors() ? $errors->get_error_message() : 'the upgrader reported a failure' ) ) : 'pages broke after the update';
	$ok  = wpu_bt_restore_item( $it['type'], $it['id'], $backup, $it['active'] );
	wpu_bt_rrmdir( $base . '/' . $cid );
	$final = $checks_on ? wpu_bt_health( $urls ) : array();
	wpu_bt_record( 'updates:rollback', array( 'item' => $it['id'], 'why' => $why, 'restored' => $ok ), false );
	return $out + array(
		'status'         => $ok ? 'rolled_back' : 'rollback_failed',
		'why'            => $why,
		'broken_pages'   => $regressions,
		'after_rollback' => $final,
		'error'          => $ok ? '' : 'The old version could not be put back. Check the site now (rescue through hosting if needed).',
	);
}

/** Replace a plugin/theme folder (or single-file plugin) with its zipped backup. */
function wpu_bt_restore_item( $type, $id, $backup, $was_active ) {
	$base = wp_normalize_path( (string) realpath( wpu_bt_private_dir( 'updates' ) ) );
	$b    = wp_normalize_path( (string) realpath( (string) $backup ) );
	if ( '' === $base || '' === $b || 0 !== strpos( $b, trailingslashit( $base ) ) || '.zip' !== substr( $b, -4 ) ) {
		return false; // the backup must be one of ours
	}
	list( $root, $target ) = wpu_bt_item_target( $type, $id );
	if ( '' === $root || basename( $target ) . '.zip' !== basename( $b ) ) {
		return false;
	}
	// The target's parent must really be the root (no links leading elsewhere).
	if ( wp_normalize_path( (string) realpath( dirname( $target ) ) ) !== $root ) {
		return false;
	}
	if ( is_link( $target ) ) {
		wp_delete_file( $target );
	} elseif ( is_dir( $target ) ) {
		wpu_bt_rrmdir_any( $target );
	} elseif ( file_exists( $target ) ) {
		wp_delete_file( $target );
	}
	$ok = wpu_bt_unzip_item( $b, $root, basename( $target ) ) && file_exists( $target );
	if ( 'plugin' === $type ) {
		wp_clean_plugins_cache();
		if ( $ok && $was_active && ! is_plugin_active( $id ) ) {
			activate_plugin( $id, '', false, true );
		}
	} else {
		wp_clean_themes_cache();
	}
	// The site now runs the old version: let WordPress offer the update again.
	delete_site_transient( 'plugin' === $type ? 'update_plugins' : 'update_themes' );
	return $ok;
}

/** Undo of an update: go back to the backed-up version. */
function wpu_bt_updates_undo( array $p ) {
	if ( '' !== wpu_bt_updates_blocker() ) {
		return wpu_bt_err( wpu_bt_updates_blocker() );
	}
	if ( ! current_user_can( 'plugin' === $p['type'] ? 'update_plugins' : 'update_themes' ) ) {
		return wpu_bt_err( 'You cannot change plugins or themes.' );
	}
	if ( empty( $p['backup'] ) || ! file_exists( $p['backup'] ) ) {
		return wpu_bt_err( 'The backup for this update was already removed (only the newest ' . WPU_BT_KEEP_BACKUPS . ' are kept).' );
	}
	$ok = wpu_bt_restore_item( $p['type'], $p['id'], $p['backup'], ! empty( $p['active'] ) );
	if ( ! $ok ) {
		return wpu_bt_err( 'Could not put the old version back.' );
	}
	$health = wpu_bt_health( wpu_bt_default_check_urls() );
	return array( 'restored' => $p['name'], 'version' => $p['from'], 'health' => $health );
}

/** Keep the newest backups only; older update changes lose their undo. */
function wpu_bt_prune_backups() {
	$base = wpu_bt_private_dir( 'updates' );
	if ( '' === $base ) {
		return;
	}
	$dirs = glob( $base . '/c*', GLOB_ONLYDIR );
	if ( ! $dirs || count( $dirs ) <= WPU_BT_KEEP_BACKUPS ) {
		return;
	}
	usort( $dirs, function ( $x, $y ) {
		return strcmp( basename( $x ), basename( $y ) ); // ids start with the date, so this is oldest first
	} );
	$drop  = array_slice( $dirs, 0, count( $dirs ) - WPU_BT_KEEP_BACKUPS );
	$index = (array) get_option( 'wpu_bt_changes', array() );
	foreach ( $drop as $d ) {
		$id = basename( $d );
		wpu_bt_rrmdir( $d );
		foreach ( $index as $i => $c ) {
			if ( isset( $c['id'] ) && $c['id'] === $id ) {
				$index[ $i ]['stored'] = false;
			}
		}
	}
	update_option( 'wpu_bt_changes', $index, false );
}
