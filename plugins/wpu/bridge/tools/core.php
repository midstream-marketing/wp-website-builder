<?php
/**
 * Shared helpers: settings, addresses, the activity log, the change log (undo), private storage and
 * the site health check used before and after updates.
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/* -------------------------------------------------------------------------
 * Settings
 * ---------------------------------------------------------------------- */

function wpu_bt_default_settings() {
	return array(
		'read_only'      => false, // every write tool refuses
		'allow_updates'  => true,  // plugin and theme updates
		'allow_orders'   => true,  // WooCommerce order changes
		'allow_themes'   => true,  // draft themes, theme previews and switching the live theme
		'builder_abilities' => false, // Breakdance / Oxygen / SeedProd AI actions that change things
		'divi_addons'    => false, // Divi modules that other plugins add (off: Divi's own modules only)
		'abilities'      => 'all', // WordPress Abilities API: all | readonly | off
	);
}

function wpu_bt_settings() {
	$s = get_option( 'wpu_bt_settings', array() );
	return array_merge( wpu_bt_default_settings(), is_array( $s ) ? $s : array() );
}

function wpu_bt_setting( $key ) {
	$s = wpu_bt_settings();
	return isset( $s[ $key ] ) ? $s[ $key ] : null;
}

function wpu_bt_is_disabled() {
	return wpu_bridge_is_disabled() || wpu_bridge_is_expired();
}

function wpu_bt_https_ok() {
	return is_ssl() || ( defined( 'WPU_BRIDGE_ALLOW_HTTP' ) && WPU_BRIDGE_ALLOW_HTTP );
}

/* -------------------------------------------------------------------------
 * Addresses
 * ---------------------------------------------------------------------- */



function wpu_bt_site_host() {
	return strtolower( (string) wp_parse_url( home_url(), PHP_URL_HOST ) );
}

/** True when $url is an http(s) address on this site's own host. */
function wpu_bt_is_own_url( $url ) {
	$p = wp_parse_url( (string) $url );
	if ( ! $p || empty( $p['host'] ) || empty( $p['scheme'] ) || ! in_array( strtolower( $p['scheme'] ), array( 'http', 'https' ), true ) ) {
		return false;
	}
	// Same scheme, host and port as the site: no other ports or services on this machine.
	$home        = wp_parse_url( home_url() );
	$port        = isset( $p['port'] ) ? (int) $p['port'] : ( 'https' === strtolower( $p['scheme'] ) ? 443 : 80 );
	$home_scheme = isset( $home['scheme'] ) ? strtolower( $home['scheme'] ) : 'https';
	$home_port   = isset( $home['port'] ) ? (int) $home['port'] : ( 'https' === $home_scheme ? 443 : 80 );
	return strtolower( $p['host'] ) === wpu_bt_site_host() && strtolower( $p['scheme'] ) === $home_scheme && $port === $home_port;
}

/* -------------------------------------------------------------------------
 * Activity log - who did what, through which app. Kept short on purpose.
 * ---------------------------------------------------------------------- */

function wpu_bt_record( $what, $details = array(), $ok = true ) {
	$entries   = get_option( 'wpu_bt_audit', array() );
	$entries   = is_array( $entries ) ? $entries : array();
	$user      = wp_get_current_user();
	$entries[] = array(
		'at'      => gmdate( 'c' ),
		'user'    => $user && $user->exists() ? $user->user_login : '',
		'app'     => isset( $GLOBALS['wpu_bridge_member'] ) ? (string) $GLOBALS['wpu_bridge_member'] : '',
		'what'    => substr( (string) $what, 0, 120 ),
		'ok'      => (bool) $ok,
		'details' => $details,
	);
	update_option( 'wpu_bt_audit', array_slice( $entries, -300 ), false );
}

/* -------------------------------------------------------------------------
 * Private storage for change records and update backups.
 * Outside the web root when possible, else a random folder in uploads with deny-all files.
 * ---------------------------------------------------------------------- */

function wpu_bt_private_dir( $sub ) {
	$sub   = sanitize_key( $sub );
	$token = get_option( 'wpu_bt_dir_token' );
	if ( ! is_string( $token ) || ! preg_match( '/^[a-z0-9]{20}$/', $token ) ) {
		$token = strtolower( wp_generate_password( 20, false ) );
		update_option( 'wpu_bt_dir_token', $token, false );
	}

	$docroot    = isset( $_SERVER['DOCUMENT_ROOT'] ) ? wp_normalize_path( (string) realpath( sanitize_text_field( wp_unslash( $_SERVER['DOCUMENT_ROOT'] ) ) ) ) : '';
	$above      = dirname( rtrim( ABSPATH, '/\\' ) );
	$above_real = wp_normalize_path( (string) realpath( $above ) );
	if ( $above_real && '' !== $docroot && 0 !== strpos( trailingslashit( $above_real ), trailingslashit( $docroot ) ) ) {
		$dir = $above . '/wpu-bridge-tools-' . $token . '/' . $sub;
		if ( wpu_bt_prepare_dir( dirname( $dir ) ) && wpu_bt_prepare_dir( $dir ) ) {
			return $dir;
		}
	}

	$up  = wp_upload_dir( null, false );
	$dir = trailingslashit( $up['basedir'] ) . 'wpu-bridge-tools-' . $token;
	if ( wpu_bt_prepare_dir( $dir ) && wpu_bt_prepare_dir( $dir . '/' . $sub ) ) {
		return $dir . '/' . $sub;
	}
	return '';
}

/** True when the private folder had to go inside uploads (inside the web root). Shown in the connection check. */
function wpu_bt_private_in_webroot() {
	$d  = wp_normalize_path( (string) wpu_bt_private_dir( 'changes' ) );
	$up = wp_upload_dir( null, false );
	return '' === $d || 0 === strpos( $d, trailingslashit( wp_normalize_path( $up['basedir'] ) ) );
}

function wpu_bt_prepare_dir( $dir ) {
	if ( ! ( is_dir( $dir ) || wp_mkdir_p( $dir ) ) || ! wp_is_writable( $dir ) || is_link( $dir ) ) {
		return false;
	}
	// Only the web server's own user may read or write here (wp_mkdir_p copies the parent's mode, which can be 0777).
	chmod( $dir, 0700 ); // phpcs:ignore WordPress.WP.AlternativeFunctions
	$deny = array(
		'.htaccess'  => "Require all denied\nDeny from all\n",
		'index.php'  => "<?php // Silence is golden.\n",
		'web.config' => '<?xml version="1.0"?><configuration><system.webServer><authorization><deny users="*" /></authorization></system.webServer></configuration>',
	);
	foreach ( $deny as $name => $body ) {
		if ( ! file_exists( $dir . '/' . $name ) ) {
			file_put_contents( $dir . '/' . $name, $body ); // phpcs:ignore WordPress.WP.AlternativeFunctions
		}
	}
	return true;
}

/* -------------------------------------------------------------------------
 * Change log - every write keeps what it replaced, so it can be undone.
 *
 * The index (small) lives in an option; the before-state (can be large: page content, Elementor data)
 * lives in a private file named by the change id.
 * ---------------------------------------------------------------------- */

/**
 * @param string $tool    tool name
 * @param string $summary one line, for people
 * @param array  $undo    array( 'kind' => ..., ... ) understood by wpu_bt_undo_apply()
 * @return string change id
 */
function wpu_bt_new_change_id() {
	return 'c' . gmdate( 'ymdHis' ) . strtolower( wp_generate_password( 6, false ) );
}

function wpu_bt_change_add( $tool, $summary, array $undo, $id = null ) {
	$id  = is_string( $id ) && preg_match( '/^c\d{12}[a-z0-9]{6}$/', $id ) ? $id : wpu_bt_new_change_id();
	$dir = wpu_bt_private_dir( 'changes' );
	if ( '' !== $dir ) {
		$json = (string) wp_json_encode( $undo );
		// Signed, so a change file edited on disk is refused instead of being written back into the site.
		file_put_contents( $dir . '/' . $id . '.json', wp_json_encode( array( 'sig' => wpu_bt_sign( $id . '|' . $json ), 'data' => $json ) ) ); // phpcs:ignore WordPress.WP.AlternativeFunctions
	}
	$index   = get_option( 'wpu_bt_changes', array() );
	$index   = is_array( $index ) ? $index : array();
	$user    = wp_get_current_user();
	$index[] = array(
		'id'      => $id,
		'at'      => gmdate( 'c' ),
		'user'    => $user && $user->exists() ? $user->user_login : '',
		'app'     => isset( $GLOBALS['wpu_bridge_member'] ) ? (string) $GLOBALS['wpu_bridge_member'] : '',
		'tool'    => $tool,
		'summary' => substr( (string) $summary, 0, 200 ),
		'kind'    => (string) $undo['kind'],
		'undone'  => false,
		'stored'  => '' !== $dir,
	);
	// Keep the newest 200; delete the files of the ones that fall off.
	while ( count( $index ) > 200 ) {
		$old = array_shift( $index );
		if ( '' !== $dir && isset( $old['id'] ) && preg_match( '/^c\d{12}[a-z0-9]{6}$/', $old['id'] ) ) {
			wp_delete_file( $dir . '/' . $old['id'] . '.json' );
			wpu_bt_rrmdir( wpu_bt_private_dir( 'updates' ) . '/' . $old['id'] );
		}
	}
	update_option( 'wpu_bt_changes', $index, false );
	return $id;
}

function wpu_bt_change_find( $id ) {
	if ( ! is_string( $id ) || ! preg_match( '/^c\d{12}[a-z0-9]{6}$/', $id ) ) {
		return null;
	}
	foreach ( (array) get_option( 'wpu_bt_changes', array() ) as $c ) {
		if ( isset( $c['id'] ) && $c['id'] === $id ) {
			return $c;
		}
	}
	return null;
}

function wpu_bt_change_mark_undone( $id ) {
	$index = (array) get_option( 'wpu_bt_changes', array() );
	foreach ( $index as $i => $c ) {
		if ( isset( $c['id'] ) && $c['id'] === $id ) {
			$index[ $i ]['undone'] = gmdate( 'c' );
		}
	}
	update_option( 'wpu_bt_changes', $index, false );
}

function wpu_bt_change_payload( $id ) {
	$dir = wpu_bt_private_dir( 'changes' );
	if ( '' === $dir || ! wpu_bt_change_find( $id ) ) {
		return null;
	}
	$file = $dir . '/' . $id . '.json';
	if ( ! is_readable( $file ) ) {
		return null;
	}
	$wrap = json_decode( (string) file_get_contents( $file ), true ); // phpcs:ignore WordPress.WP.AlternativeFunctions
	if ( ! is_array( $wrap ) || ! isset( $wrap['sig'], $wrap['data'] ) || ! is_string( $wrap['data'] ) || ! hash_equals( wpu_bt_sign( $id . '|' . $wrap['data'] ), (string) $wrap['sig'] ) ) {
		return null; // unsigned (older version) or altered on disk
	}
	$data = json_decode( $wrap['data'], true );
	return is_array( $data ) ? $data : null;
}

/**
 * Delete everything the tools stored: undo copies, update backups, the change list, the activity list,
 * preview links and the switches. Called when the bridge is activated and when it is deactivated.
 * Draft themes are left: they are themes on the site now, and one may be the active theme.
 */
function wpu_bt_purge() {
	$token = get_option( 'wpu_bt_dir_token' );
	if ( is_string( $token ) && preg_match( '/^[a-z0-9]{20}$/', $token ) ) {
		$up = wp_upload_dir( null, false );
		foreach ( array( dirname( rtrim( ABSPATH, '/\\' ) ), isset( $up['basedir'] ) ? $up['basedir'] : '' ) as $base ) {
			$dir = '' === $base ? '' : rtrim( $base, '/\\' ) . '/wpu-bridge-tools-' . $token;
			if ( '' !== $dir && is_dir( $dir ) && ! is_link( $dir ) ) {
				wpu_bt_rrmdir_any( $dir );
			}
		}
	}
	foreach ( array( 'wpu_bt_changes', 'wpu_bt_audit', 'wpu_bt_theme_previews', 'wpu_bt_settings', 'wpu_bt_dir_token' ) as $opt ) {
		delete_option( $opt );
	}
}

function wpu_bt_sign( $text ) {
	// The activation time is part of the key, so undo records from an earlier install of the bridge stop working.
	return hash_hmac( 'sha256', (string) $text, wp_salt( 'auth' ) . '|wpu-bridge-tools-changes|' . (int) get_option( 'wpu_bridge_activated', 0 ) );
}

/** Delete a folder tree that this plugin made inside its private folder. */
function wpu_bt_rrmdir( $dir ) {
	$base = wpu_bt_private_dir( 'updates' );
	if ( '' === $base || ! is_dir( $dir ) ) {
		return;
	}
	$real = wp_normalize_path( (string) realpath( $dir ) );
	$root = wp_normalize_path( (string) realpath( dirname( $base ) ) );
	if ( '' === $real || '' === $root || 0 !== strpos( $real, trailingslashit( $root ) ) ) {
		return; // never outside our own folder
	}
	wpu_bt_rrmdir_any( $real );
}

/** Recursive delete. Callers make sure $dir is one of ours (a backup, or a plugin/theme folder being restored). */
function wpu_bt_rrmdir_any( $dir ) {
	if ( is_link( $dir ) ) {
		wp_delete_file( $dir );
		return;
	}
	if ( ! is_dir( $dir ) ) {
		return;
	}
	$items = scandir( $dir );
	foreach ( (array) $items as $item ) {
		if ( '.' === $item || '..' === $item ) {
			continue;
		}
		$p = $dir . '/' . $item;
		if ( is_dir( $p ) && ! is_link( $p ) ) {
			wpu_bt_rrmdir_any( $p );
		} else {
			wp_delete_file( $p );
		}
	}
	rmdir( $dir ); // phpcs:ignore WordPress.WP.AlternativeFunctions
}

/* -------------------------------------------------------------------------
 * Health check: load pages the way a visitor does and look for breakage.
 * Used by site_health_check and before/after every update.
 * ---------------------------------------------------------------------- */

/** Pages checked when none are given: home, newest post, newest page, and the shop and cart pages if WooCommerce runs. */
function wpu_bt_default_check_urls() {
	$urls = array( home_url( '/' ) );
	foreach ( array( 'post', 'page' ) as $type ) {
		$p = get_posts( array( 'post_type' => $type, 'post_status' => 'publish', 'numberposts' => 1, 'orderby' => 'date', 'order' => 'DESC', 'fields' => 'ids' ) );
		if ( $p ) {
			$urls[] = get_permalink( $p[0] );
		}
	}
	if ( function_exists( 'wc_get_page_permalink' ) ) {
		foreach ( array( 'shop', 'cart' ) as $page ) {
			$u = wc_get_page_permalink( $page );
			if ( $u && wpu_bt_is_own_url( $u ) ) {
				$urls[] = $u;
			}
		}
	}
	return array_values( array_unique( array_filter( $urls ) ) );
}

/** @return array list of url results */
function wpu_bt_health( array $urls ) {
	$out = array();
	foreach ( array_slice( $urls, 0, 10 ) as $url ) {
		if ( ! wpu_bt_is_own_url( $url ) ) {
			$out[] = array( 'url' => (string) $url, 'ok' => false, 'error' => 'not an address on this site' );
			continue;
		}
		$t0   = microtime( true );
		$resp = wp_remote_get( // wpsec:ignore - only addresses on this site's own host (checked above); safe_remote would refuse a site that resolves to itself
			add_query_arg( 'wpu_check', wp_generate_password( 8, false ), $url ),
			array(
				'timeout'     => 20,
				'redirection' => 0, // a redirect counts as a working page; it is never followed (it could lead off the site)
				'sslverify'   => apply_filters( 'https_local_ssl_verify', false ), // same loopback rule core uses
				'headers'     => array( 'Cache-Control' => 'no-cache' ),
				'user-agent'  => 'WPU-Bridge-HealthCheck/' . WPU_BT_VERSION,
			)
		);
		$ms = (int) round( ( microtime( true ) - $t0 ) * 1000 );
		if ( is_wp_error( $resp ) ) {
			$out[] = array( 'url' => $url, 'ok' => false, 'status' => 0, 'ms' => $ms, 'error' => $resp->get_error_message() );
			continue;
		}
		$code   = (int) wp_remote_retrieve_response_code( $resp );
		$body   = (string) wp_remote_retrieve_body( $resp );
		$marker = '';
		foreach ( array( 'There has been a critical error', 'Fatal error</b>', 'Parse error</b>', 'Briefly unavailable for scheduled maintenance', 'Error establishing a database connection' ) as $m ) {
			if ( false !== stripos( $body, $m ) ) {
				$marker = wp_strip_all_tags( $m );
				break;
			}
		}
		$title = '';
		if ( preg_match( '/<title[^>]*>(.*?)<\/title>/is', $body, $mt ) ) {
			$title = trim( wp_strip_all_tags( html_entity_decode( $mt[1], ENT_QUOTES ) ) );
		}
		$out[] = array(
			'url'    => $url,
			'ok'     => $code >= 200 && $code < 400 && '' === $marker,
			'status' => $code,
			'ms'     => $ms,
			'bytes'  => strlen( $body ),
			'title'  => substr( $title, 0, 120 ),
			'error'  => $marker,
		);
	}
	return $out;
}

/**
 * Compare two health runs. A page that worked before and fails now is a regression.
 * A page that was already broken is reported, not blamed on the update.
 */
function wpu_bt_health_regressions( array $before, array $after ) {
	$was = array();
	foreach ( $before as $r ) {
		$was[ $r['url'] ] = ! empty( $r['ok'] );
	}
	$bad = array();
	foreach ( $after as $r ) {
		if ( ! empty( $was[ $r['url'] ] ) && empty( $r['ok'] ) ) {
			$bad[] = $r;
		}
	}
	return $bad;
}

/* -------------------------------------------------------------------------
 * Visible text vs markup. Everything that is not plain text stays untouched by text replacement:
 * comments (block attributes), whole <script>, <style> and <textarea> elements, and tags parsed with
 * their quoted attributes (a ">" inside an attribute does not end the tag).
 * ---------------------------------------------------------------------- */

const WPU_BT_NONTEXT = '/(<!--.*?-->|<script\b.*?<\/script\s*>|<style\b.*?<\/style\s*>|<textarea\b.*?<\/textarea\s*>|<(?:[^>"\']|"[^"]*"|\'[^\']*\')*>)/is';

/** Split markup: even indexes are visible text, odd indexes are markup. $extra adds alternatives (e.g. shortcodes). */
function wpu_bt_split_markup( $content, $extra = '' ) {
	$re = '' === $extra ? WPU_BT_NONTEXT : str_replace( '/(<!--', '/(' . $extra . '|<!--', WPU_BT_NONTEXT );
	$parts = preg_split( $re, (string) $content, -1, PREG_SPLIT_DELIM_CAPTURE );
	return false === $parts ? array( (string) $content ) : $parts;
}

/* -------------------------------------------------------------------------
 * Small helpers for tools
 * ---------------------------------------------------------------------- */

function wpu_bt_err( $message, $code = 'wpu_bt_error' ) {
	return new WP_Error( $code, $message );
}

function wpu_bt_trim( $s, $max = 60000 ) {
	$s = (string) $s;
	return strlen( $s ) > $max ? substr( $s, 0, $max ) . "\n... [" . ( strlen( $s ) - $max ) . ' more characters cut]' : $s;
}

function wpu_bt_int( array $a, $key, $default = 0, $min = 0, $max = PHP_INT_MAX ) {
	$v = isset( $a[ $key ] ) ? (int) $a[ $key ] : (int) $default;
	return max( $min, min( $max, $v ) );
}

function wpu_bt_str( array $a, $key, $default = '' ) {
	return isset( $a[ $key ] ) && is_scalar( $a[ $key ] ) ? (string) $a[ $key ] : (string) $default;
}

function wpu_bt_bool( array $a, $key, $default = false ) {
	if ( ! array_key_exists( $key, $a ) ) {
		return (bool) $default;
	}
	return filter_var( $a[ $key ], FILTER_VALIDATE_BOOLEAN );
}
