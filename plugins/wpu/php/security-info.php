<?php
/**
 * Read-only security overview: core/plugin/theme updates, risky plugins, users and roles,
 * application passwords, file editing, debug output, XML-RPC, REST user listing, author
 * enumeration, registration role, salts, HTTPS, uploads PHP, readme/license exposure.
 *
 *   powershell -File bin/rwpphp.ps1 php/security-info.php
 */

defined( 'ABSPATH' ) || exit;

require_once ABSPATH . 'wp-admin/includes/plugin.php';
require_once ABSPATH . 'wp-admin/includes/update.php';

global $wp_version;
wp_update_plugins();
wp_update_themes();
$core = get_preferred_from_update_core();
printf( "WordPress %s | core update: %s | PHP %s\n", $wp_version, ( $core && 'upgrade' === $core->response ) ? $core->current : 'none', PHP_VERSION );

echo "\n=== plugins ===\n";
$updates = get_site_transient( 'update_plugins' );
foreach ( get_plugins() as $file => $d ) {
	$upd = isset( $updates->response[ $file ] ) ? ' UPDATE -> ' . $updates->response[ $file ]->new_version : '';
	printf( "  %-8s %-52s %-9s%s\n", is_plugin_active( $file ) ? 'ACTIVE' : 'inactive', mb_strimwidth( $file, 0, 52 ), $d['Version'], $upd );
}
echo "mu-plugins: " . implode( ', ', array_keys( get_mu_plugins() ) ) . "\n";
$tupd = get_site_transient( 'update_themes' );
foreach ( wp_get_themes() as $slug => $t ) {
	printf( "  theme %-22s %-8s%s%s\n", $slug, $t->get( 'Version' ), get_stylesheet() === $slug || get_template() === $slug ? ' (in use)' : '', isset( $tupd->response[ $slug ] ) ? ' UPDATE -> ' . $tupd->response[ $slug ]['new_version'] : '' );
}

echo "\n=== users ===\n";
foreach ( get_users( array( 'role__in' => array( 'administrator', 'editor', 'shop_manager' ) ) ) as $u ) {
	$ap = class_exists( 'WP_Application_Passwords' ) ? count( WP_Application_Passwords::get_user_application_passwords( $u->ID ) ) : 0;
	printf( "  #%-4d %-20s %-26s %-14s app-passwords:%d registered:%s\n", $u->ID, $u->user_login, $u->user_email, implode( ',', $u->roles ), $ap, $u->user_registered );
}
$counts = count_users();
printf( "  totals: %s\n", wp_json_encode( $counts['avail_roles'] ) );
printf( "  'admin' username exists: %s\n", username_exists( 'admin' ) ? 'YES' : 'no' );
printf( "  default role for new users: %s | anyone can register (WP): %s | Woo registration: %s\n", get_option( 'default_role' ), get_option( 'users_can_register' ) ? 'yes' : 'no', get_option( 'woocommerce_enable_myaccount_registration' ) );

echo "\n=== hardening ===\n";
printf( "  DISALLOW_FILE_EDIT: %s | DISALLOW_FILE_MODS: %s\n", defined( 'DISALLOW_FILE_EDIT' ) && DISALLOW_FILE_EDIT ? 'on' : 'OFF', defined( 'DISALLOW_FILE_MODS' ) && DISALLOW_FILE_MODS ? 'on' : 'off' );
printf( "  WP_DEBUG: %s | WP_DEBUG_DISPLAY: %s | display_errors: %s\n", WP_DEBUG ? 'ON' : 'off', ( defined( 'WP_DEBUG_DISPLAY' ) ? ( WP_DEBUG_DISPLAY ? 'on' : 'off' ) : 'default' ), ini_get( 'display_errors' ) );
printf( "  XML-RPC enabled filter: %s\n", apply_filters( 'xmlrpc_enabled', true ) ? 'enabled' : 'disabled' );
printf( "  siteurl/home https: %s / %s | FORCE_SSL_ADMIN: %s\n", wp_parse_url( get_option( 'siteurl' ), PHP_URL_SCHEME ), wp_parse_url( get_option( 'home' ), PHP_URL_SCHEME ), defined( 'FORCE_SSL_ADMIN' ) && FORCE_SSL_ADMIN ? 'on' : 'off' );
printf( "  salts set: %s | table prefix: %s\n", ( defined( 'AUTH_KEY' ) && strlen( AUTH_KEY ) > 30 && false === strpos( AUTH_KEY, 'put your' ) ) ? 'yes' : 'NO', $GLOBALS['wpdb']->prefix );
printf( "  blog public (search engines): %s\n", get_option( 'blog_public' ) ? 'indexed' : 'discouraged' );
foreach ( array( 'readme.html', 'license.txt', 'wp-config-sample.php', '.user.ini', 'debug.log', 'wp-content/debug.log' ) as $f ) {
	if ( file_exists( ABSPATH . $f ) ) {
		printf( "  exposed file present: /%s (%d bytes)\n", $f, filesize( ABSPATH . $f ) );
	}
}
$up = wp_get_upload_dir()['basedir'];
$php_in_uploads = array();
$it = new RecursiveIteratorIterator( new RecursiveDirectoryIterator( $up, FilesystemIterator::SKIP_DOTS ) );
foreach ( $it as $file ) {
	if ( preg_match( '/\.(php|phtml|phar)$/i', $file->getFilename() ) && false === strpos( $file->getPathname(), 'index.php' ) ) {
		$php_in_uploads[] = str_replace( $up, '', $file->getPathname() );
	}
	if ( count( $php_in_uploads ) > 20 ) {
		break;
	}
}
printf( "  PHP files in uploads: %d %s\n", count( $php_in_uploads ), implode( ' ', array_slice( $php_in_uploads, 0, 10 ) ) );
