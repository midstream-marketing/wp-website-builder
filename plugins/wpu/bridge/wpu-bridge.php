<?php
/**
 * Plugin Name:  WPU Bridge
 * Description:  TEMPORARY build-time bridge for the WP Ultimate Build toolkit
 *               (Claude Code). Lets the toolkit build, fix and optimise this site
 *               over an authenticated REST endpoint - pages, Elementor templates,
 *               media, SEO fields, posts and maintenance scripts - with no
 *               hosting access. DELETE THIS PLUGIN AT HANDOVER - it
 *               self-deactivates after 30 days regardless.
 * Version:      2.0.0
 * Requires PHP: 7.4
 * Author:       Webelite Digital
 *
 * Merged from WP Site Doctor Bridge 1.4.0 (wpsd/v1) and WP Site Build Bridge
 * 1.0.0 (wpsb/v1). New namespace wpu/v1, so it installs beside either of them.
 * 2.0.0 adds: /media and /template (from the build bridge), /seo and /posts
 * (typed routes so routine SEO and blog work never needs /run), and one
 * connection key per team member, so the audit log says who ran what.
 *
 * ---------------------------------------------------------------------------
 * WHAT THIS IS, STATED PLAINLY
 *
 * The /run route executes PHP you send it. That is remote code execution, and
 * it is the point: the toolkit is ~150 one-off scripts and they must run
 * unchanged. It is not a new privilege - an administrator can already do this
 * through Plugins > Add New > Upload, or the file editor. This is a second door
 * into the same room, so the whole job is making the door as strong as the
 * front one:
 *
 *   - administrator capability required on every route (manage_options)
 *   - authenticated by a per-member connection key made under Tools > WPU
 *     Bridge (only its hash is stored, it is tied to the admin who made it, it
 *     carries the member's name into the audit log, and all keys are deleted on
 *     deactivation), or by a WordPress Application Password. Keys exist for
 *     sites where a firewall blocks the Application Passwords screen.
 *   - HTTPS enforced unless WPU_BRIDGE_ALLOW_HTTP is defined (local testing)
 *   - hard expiry - the routes stop existing and the plugin deactivates itself
 *   - every call recorded with user, time and what was run
 *   - one-line kill switch: define('WPU_BRIDGE_DISABLE', true) in wp-config.php
 *
 * The expiry exists because the realistic failure is not an attack, it is
 * forgetting to remove this at handover. Forgetting now fails safe.
 * ---------------------------------------------------------------------------
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/*
 * 1.1.0 — output capture rewritten after testing on LocalWP. 1.0.0 lost a
 * script's entire output on any exit(), which is every dry run. If a site
 * reports 1.0.0 from /doctor, replace it. See docs/GOTCHAS.md.
 */
define( 'WPU_BRIDGE_VERSION', '2.0.0' );
define( 'WPU_BRIDGE_NS', 'wpu/v1' );

/** Days from activation until the bridge switches itself off. */
if ( ! defined( 'WPU_BRIDGE_DAYS' ) ) {
	define( 'WPU_BRIDGE_DAYS', 30 );
}

/* -------------------------------------------------------------------------
 * Lifecycle
 * ---------------------------------------------------------------------- */

register_activation_hook( __FILE__, 'wpu_bridge_activate' );
function wpu_bridge_activate() {
	update_option( 'wpu_bridge_activated', time(), false );
	// A plugin folder deleted over FTP never runs the deactivation hook, so old
	// keys would come back to life on a re-install. Every activation starts clean.
	delete_option( 'wpu_bridge_keys' );
	delete_option( 'wpu_bridge_audit' );
}

register_deactivation_hook( __FILE__, 'wpu_bridge_deactivate' );
function wpu_bridge_deactivate() {
	delete_option( 'wpu_bridge_activated' );
	delete_option( 'wpu_bridge_keys' );
}

function wpu_bridge_activated_at() {
	$t = (int) get_option( 'wpu_bridge_activated', 0 );
	if ( ! $t ) {
		// Dropped in by file copy rather than activated through wp-admin.
		$t = time();
		update_option( 'wpu_bridge_activated', $t, false );
	}
	return $t;
}

function wpu_bridge_expires_at() {
	return wpu_bridge_activated_at() + ( WPU_BRIDGE_DAYS * DAY_IN_SECONDS );
}

function wpu_bridge_is_expired() {
	return time() > wpu_bridge_expires_at();
}

function wpu_bridge_is_disabled() {
	return defined( 'WPU_BRIDGE_DISABLE' ) && WPU_BRIDGE_DISABLE;
}

/**
 * Turn itself off once expired. Runs in admin only, because deactivate_plugins()
 * needs plugin.php and there is no reason to pay for this on front-end hits.
 */
add_action( 'admin_init', function () {
	if ( ! wpu_bridge_is_expired() ) {
		return;
	}
	require_once ABSPATH . 'wp-admin/includes/plugin.php';
	deactivate_plugins( plugin_basename( __FILE__ ) );
} );

add_action( 'admin_notices', function () {
	if ( ! defined( 'WPU_BRIDGE_NOTICE' ) || ! WPU_BRIDGE_NOTICE ) {
		return; // off by default since 1.3.0, see the header comment
	}
	if ( ! current_user_can( 'manage_options' ) ) {
		return;
	}
	$left = wpu_bridge_expires_at() - time();
	if ( $left <= 0 ) {
		$msg   = 'WP WPU Bridge has expired and switched itself off. Delete the plugin.';
		$class = 'notice-error';
	} else {
		$days  = max( 1, (int) ceil( $left / DAY_IN_SECONDS ) );
		$msg   = sprintf(
			'WP WPU Bridge is active - a build-time remote access tool. It switches itself off in %d day%s. Delete it before handover.',
			$days,
			1 === $days ? '' : 's'
		);
		$class = 'notice-warning';
	}
	printf( '<div class="notice %s"><p><strong>%s</strong></p></div>', esc_attr( $class ), esc_html( $msg ) );
} );

/* -------------------------------------------------------------------------
 * Some hosts (CGI/FastCGI) drop the Authorization header before PHP sees it,
 * which makes Application Passwords fail with no useful signal. Recover it from
 * the places Apache and friends stash it.
 * ---------------------------------------------------------------------- */

add_action( 'plugins_loaded', function () {
	if ( ! empty( $_SERVER['HTTP_AUTHORIZATION'] ) ) {
		return;
	}
	foreach ( array( 'REDIRECT_HTTP_AUTHORIZATION', 'HTTP_X_AUTHORIZATION' ) as $k ) {
		if ( ! empty( $_SERVER[ $k ] ) ) {
			$_SERVER['HTTP_AUTHORIZATION'] = $_SERVER[ $k ];
			return;
		}
	}
	if ( function_exists( 'apache_request_headers' ) ) {
		foreach ( (array) apache_request_headers() as $name => $value ) {
			if ( 0 === strcasecmp( $name, 'Authorization' ) ) {
				$_SERVER['HTTP_AUTHORIZATION'] = $value;
				return;
			}
		}
	}
}, 1 );

/**
 * While a script is running, stop WordPress's own fatal-error handler from
 * answering. Left alone it emits its "critical error" JSON with a 500 from a
 * shutdown function registered at bootstrap - i.e. before ours - so the client
 * receives core's error page with our result glued onto the end, and the real
 * message is buried. We would rather report the fatal ourselves.
 */
add_filter( 'wp_should_handle_php_error', function ( $handle ) {
	if ( ! empty( $GLOBALS['wpu_bridge_running'] ) ) {
		return false;
	}
	return $handle;
}, 10, 1 );

/** Application Passwords are refused over plain HTTP by core. Allow opt-in for local testing. */
add_filter( 'wp_is_application_passwords_available', function ( $available ) {
	if ( defined( 'WPU_BRIDGE_ALLOW_HTTP' ) && WPU_BRIDGE_ALLOW_HTTP ) {
		return true;
	}
	return $available;
} );

/* -------------------------------------------------------------------------
 * Routes
 * ---------------------------------------------------------------------- */

add_action( 'rest_api_init', function () {

	if ( wpu_bridge_is_disabled() || wpu_bridge_is_expired() ) {
		return; // routes simply do not exist
	}

	$auth = array( 'permission_callback' => 'wpu_bridge_permission' );

	register_rest_route( WPU_BRIDGE_NS, '/doctor', $auth + array(
		'methods'  => 'GET',
		'callback' => 'wpu_bridge_doctor',
	) );

	// Routes that run or write code need the right to change code, not just manage_options.
	$code_auth = array( 'permission_callback' => 'wpu_bridge_permission_code' );

	register_rest_route( WPU_BRIDGE_NS, '/run', $code_auth + array(
		'methods'  => 'POST',
		'callback' => 'wpu_bridge_run',
	) );

	register_rest_route( WPU_BRIDGE_NS, '/log', $auth + array(
		'methods'  => 'GET',
		'callback' => 'wpu_bridge_log',
	) );

	register_rest_route( WPU_BRIDGE_NS, '/file', $code_auth + array(
		'methods'  => array( 'GET', 'POST' ),
		'callback' => 'wpu_bridge_file',
	) );

	register_rest_route( WPU_BRIDGE_NS, '/audit', $auth + array(
		'methods'  => 'GET',
		'callback' => 'wpu_bridge_audit',
	) );

	// Build routes (from the WP Site Build Bridge): media into the library,
	// Elementor templates into the template library.
	register_rest_route( WPU_BRIDGE_NS, '/media', $auth + array(
		'methods'  => 'POST',
		'callback' => 'wpu_bridge_media',
	) );

	register_rest_route( WPU_BRIDGE_NS, '/template', $auth + array(
		'methods'  => 'POST',
		'callback' => 'wpu_bridge_template',
	) );

	// Typed routes added in 2.0.0. Each one does one job and takes data, not
	// code, so SEO and blog work never needs /run.
	register_rest_route( WPU_BRIDGE_NS, '/seo', $auth + array(
		'methods'  => array( 'GET', 'POST' ),
		'callback' => 'wpu_bridge_seo',
	) );

	register_rest_route( WPU_BRIDGE_NS, '/seo/rollback', $auth + array(
		'methods'  => 'POST',
		'callback' => 'wpu_bridge_seo_rollback',
	) );

	register_rest_route( WPU_BRIDGE_NS, '/posts', $auth + array(
		'methods'  => array( 'GET', 'POST' ),
		'callback' => 'wpu_bridge_posts',
	) );
} );

/**
 * /run and /file: the caller must be allowed to change the site's code.
 * - DISALLOW_FILE_MODS means the owner has locked code changes; the bridge honours it.
 * - On multisite only a super admin may (a single-site admin has manage_options but not code rights).
 * - install_plugins, not edit_plugins: DISALLOW_FILE_EDIT (our own hardening) removes edit_plugins
 *   but is about the wp-admin code editor, not about deployments.
 */
function wpu_bridge_permission_code( WP_REST_Request $request ) {
	$ok = wpu_bridge_permission( $request );
	if ( true !== $ok ) {
		return $ok;
	}
	if ( defined( 'DISALLOW_FILE_MODS' ) && DISALLOW_FILE_MODS ) {
		return new WP_Error( 'wpu_file_mods', 'This site sets DISALLOW_FILE_MODS, so code changes through the bridge are refused. Use the typed routes (/seo, /posts, /media, /template) or ask the owner.', array( 'status' => 403 ) );
	}
	if ( is_multisite() && ! is_super_admin() ) {
		return new WP_Error( 'wpu_forbidden', 'On multisite, /run and /file need a super admin.', array( 'status' => 403 ) );
	}
	if ( ! current_user_can( 'install_plugins' ) ) {
		return new WP_Error( 'wpu_forbidden', 'The install_plugins capability is required for /run and /file.', array( 'status' => 403 ) );
	}
	return true;
}

function wpu_bridge_permission( WP_REST_Request $request ) {
	if ( ! is_ssl() && ! ( defined( 'WPU_BRIDGE_ALLOW_HTTP' ) && WPU_BRIDGE_ALLOW_HTTP ) ) {
		return new WP_Error(
			'wpu_insecure',
			'Refusing to run over plain HTTP. Use HTTPS, or define WPU_BRIDGE_ALLOW_HTTP for local testing.',
			array( 'status' => 403 )
		);
	}

	// Checked here rather than in determine_current_user, so the key only ever
	// logs anyone in for this plugin's own routes.
	$key = (string) $request->get_header( 'x_wpu_key' );
	if ( '' !== $key ) {
		$user_id = wpu_bridge_key_user( $key );
		if ( ! $user_id ) {
			return new WP_Error(
				'wpu_bad_key',
				'Connection key not recognised. Make a new one under Tools > WPU Bridge.',
				array( 'status' => 401 )
			);
		}
		wp_set_current_user( $user_id );
	}

	if ( ! is_user_logged_in() ) { // wpsec:ignore - manage_options is checked just below
		return new WP_Error(
			'wpu_unauthenticated',
			'Not authenticated. Send the connection key as an X-WPU-Key header, or an Application Password as HTTP Basic auth.',
			array( 'status' => 401 )
		);
	}
	if ( ! current_user_can( 'manage_options' ) ) {
		return new WP_Error( 'wpu_forbidden', 'Administrator capability required.', array( 'status' => 403 ) );
	}
	return true;
}

/* -------------------------------------------------------------------------
 * Connection key
 *
 * Application Passwords are made on the profile screen through the core REST
 * route /wp/v2/users/<id>/application-passwords. Firewalls that block user
 * enumeration (Sucuri on createdequal.org) block that route too, and the
 * screen shows an empty red error. The key is made with a normal wp-admin
 * form instead, so nothing outside this plugin's routes is involved.
 * ---------------------------------------------------------------------- */

/**
 * Keys are stored as a list, one per team member:
 *   [ { id, label, hash, user, created, last_used } ]
 * Only the SHA-256 hash is kept. The label (the member's name, typed by the
 * admin who makes the key) is written into every audit entry made with it.
 */
function wpu_bridge_keys() {
	$keys = get_option( 'wpu_bridge_keys', array() );
	return is_array( $keys ) ? array_values( $keys ) : array();
}

/** The key record that matches, or null. Its admin must still be an admin. */
function wpu_bridge_key_match( $key ) {
	$hash = hash( 'sha256', (string) $key );
	foreach ( wpu_bridge_keys() as $rec ) {
		if ( empty( $rec['hash'] ) || empty( $rec['user'] ) ) {
			continue;
		}
		if ( hash_equals( (string) $rec['hash'], $hash ) ) {
			$user = get_userdata( (int) $rec['user'] );
			if ( ! $user || ! user_can( $user, 'manage_options' ) ) {
				return null;
			}
			return $rec;
		}
	}
	return null;
}

/** The admin the key belongs to, or 0. Also remembers which member is calling. */
function wpu_bridge_key_user( $key ) {
	$rec = wpu_bridge_key_match( $key );
	if ( ! $rec ) {
		return 0;
	}
	$GLOBALS['wpu_bridge_member'] = (string) $rec['label'];

	// last_used is updated at most once an hour to keep option writes rare.
	if ( empty( $rec['last_used'] ) || (int) $rec['last_used'] < time() - HOUR_IN_SECONDS ) {
		$keys = wpu_bridge_keys();
		foreach ( $keys as $i => $k ) {
			if ( isset( $k['id'] ) && $k['id'] === $rec['id'] ) {
				$keys[ $i ]['last_used'] = time();
			}
		}
		update_option( 'wpu_bridge_keys', $keys, false );
	}
	return (int) $rec['user'];
}

add_action( 'admin_menu', function () {
	add_management_page( 'WPU Bridge', 'WPU Bridge', 'manage_options', 'wpu-bridge', 'wpu_bridge_admin_page' );
} );

function wpu_bridge_admin_page() {
	if ( ! current_user_can( 'manage_options' ) ) {
		wp_die( esc_html( 'Not allowed.' ), 403 );
	}

	$new_key   = '';
	$new_label = '';
	if ( isset( $_POST['wpu_bridge_action'] ) ) {
		check_admin_referer( 'wpu_bridge_key' );
		$action = sanitize_key( wp_unslash( $_POST['wpu_bridge_action'] ) );
		$keys   = wpu_bridge_keys();

		if ( 'generate' === $action ) {
			$label = isset( $_POST['wpu_bridge_label'] ) ? sanitize_text_field( wp_unslash( $_POST['wpu_bridge_label'] ) ) : '';
			$label = '' === $label ? wp_get_current_user()->user_login : substr( $label, 0, 60 );
			if ( count( $keys ) >= 20 ) {
				add_settings_error( 'wpu_bridge', 'wpu_full', 'Twenty keys already exist. Revoke one first.' );
			} else {
				// Shown once on this screen and never stored in plain text.
				$new_key   = 'wpu_' . wp_generate_password( 40, false );
				$new_label = $label;
				$keys[]    = array(
					'id'        => wp_generate_password( 10, false ),
					'label'     => $label,
					'hash'      => hash( 'sha256', $new_key ),
					'user'      => get_current_user_id(),
					'created'   => time(),
					'last_used' => 0,
				);
				update_option( 'wpu_bridge_keys', $keys, false );
				wpu_bridge_record( 'key:created:' . $label, 0, array() );
			}
		} elseif ( 'revoke' === $action ) {
			$id   = isset( $_POST['wpu_bridge_key_id'] ) ? sanitize_key( wp_unslash( $_POST['wpu_bridge_key_id'] ) ) : '';
			$kept = array();
			foreach ( $keys as $k ) {
				if ( isset( $k['id'] ) && strtolower( (string) $k['id'] ) === $id ) {
					wpu_bridge_record( 'key:revoked:' . $k['label'], 0, array() );
					continue;
				}
				$kept[] = $k;
			}
			update_option( 'wpu_bridge_keys', $kept, false );
		}
	}

	$keys   = wpu_bridge_keys();
	$config = wp_json_encode( array(
		'url'  => home_url(),
		'auth' => 'key',
	), JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES );
	$fmt    = get_option( 'date_format' ) . ' ' . get_option( 'time_format' );
	?>
	<div class="wrap">
		<h1>WPU Bridge</h1>
		<?php settings_errors( 'wpu_bridge' ); ?>
		<p>
			Remote build and maintenance access for the WP Ultimate Build toolkit. It switches itself off on
			<strong><?php echo esc_html( wp_date( get_option( 'date_format' ), wpu_bridge_expires_at() ) ); ?></strong>.
			Delete the plugin when the work is finished.
		</p>

		<?php if ( $new_key ) : ?>
			<div class="notice notice-success inline">
				<p><strong>New connection key for <?php echo esc_html( $new_label ); ?>.</strong> Copy it now, it is not shown again.</p>
			</div>
			<p><input type="text" class="large-text code" readonly value="<?php echo esc_attr( $new_key ); ?>" onclick="this.select();"></p>
			<p>Save it on the member's own computer with <code>wpu-secret set &lt;site&gt; key</code>, never in a project file. The <code>remote</code> block for <code>site.json</code> is:</p>
			<textarea class="large-text code" rows="5" readonly onclick="this.select();"><?php echo esc_textarea( $config ); ?></textarea>
		<?php endif; ?>

		<h2>Keys</h2>
		<?php if ( ! $keys ) : ?>
			<p>No connection keys yet.</p>
		<?php else : ?>
			<table class="widefat striped" style="max-width:900px">
				<thead><tr><th>Member</th><th>Made by</th><th>Created</th><th>Last used</th><th></th></tr></thead>
				<tbody>
				<?php foreach ( $keys as $k ) : ?>
					<?php $owner = get_userdata( (int) $k['user'] ); ?>
					<tr>
						<td><?php echo esc_html( (string) $k['label'] ); ?></td>
						<td><?php echo esc_html( $owner ? $owner->user_login : '(deleted user)' ); ?></td>
						<td><?php echo esc_html( wp_date( $fmt, (int) $k['created'] ) ); ?></td>
						<td><?php echo esc_html( empty( $k['last_used'] ) ? 'never' : wp_date( $fmt, (int) $k['last_used'] ) ); ?></td>
						<td>
							<form method="post">
								<?php wp_nonce_field( 'wpu_bridge_key' ); ?>
								<input type="hidden" name="wpu_bridge_action" value="revoke">
								<input type="hidden" name="wpu_bridge_key_id" value="<?php echo esc_attr( (string) $k['id'] ); ?>">
								<?php submit_button( 'Revoke', 'delete small', 'submit', false ); ?>
							</form>
						</td>
					</tr>
				<?php endforeach; ?>
				</tbody>
			</table>
		<?php endif; ?>

		<h2>Make a key</h2>
		<form method="post">
			<?php wp_nonce_field( 'wpu_bridge_key' ); ?>
			<input type="hidden" name="wpu_bridge_action" value="generate">
			<p>
				<label for="wpu_bridge_label">Team member's name</label><br>
				<input type="text" id="wpu_bridge_label" name="wpu_bridge_label" class="regular-text" maxlength="60" placeholder="e.g. Ashish">
			</p>
			<?php submit_button( 'Make a connection key', 'primary', 'submit', false ); ?>
		</form>
	</div>
	<?php
}

/* -------------------------------------------------------------------------
 * /doctor - report the environment before trusting it.
 *
 * Written because the first failure on an unfamiliar host is otherwise
 * indistinguishable from the bridge being broken.
 * ---------------------------------------------------------------------- */

function wpu_bridge_doctor() {
	global $wp_version, $wpdb;

	$security = array();
	$known    = array(
		'wordfence/wordfence.php'                             => 'Wordfence',
		'better-wp-security/better-wp-security.php'           => 'Solid Security',
		'sucuri-scanner/sucuri.php'                           => 'Sucuri',
		'all-in-one-wp-security-and-firewall/wp-security.php' => 'All In One WP Security',
		'ninjafirewall/ninjafirewall.php'                     => 'NinjaFirewall',
	);
	$active   = (array) get_option( 'active_plugins', array() );
	foreach ( $known as $file => $label ) {
		if ( in_array( $file, $active, true ) ) {
			$security[] = $label;
		}
	}

	$time_limit = ini_get( 'max_execution_time' );
	$can_set    = @set_time_limit( 0 );

	return rest_ensure_response( array(
		'ok'     => true,
		'bridge' => array(
			'version'    => WPU_BRIDGE_VERSION,
			'expires_at' => gmdate( 'c', wpu_bridge_expires_at() ),
			'days_left'  => (int) ceil( ( wpu_bridge_expires_at() - time() ) / DAY_IN_SECONDS ),
		),
		'site'   => array(
			'url'       => home_url(),
			'wp'        => $wp_version,
			'php'       => PHP_VERSION,
			'mysql'     => $wpdb->db_version(),
			'is_ssl'    => is_ssl(),
			'multisite' => is_multisite(),
			'user'      => wp_get_current_user()->user_login,
		),
		'limits' => array(
			'memory_limit'         => ini_get( 'memory_limit' ),
			'max_execution_time'   => $time_limit,
			'set_time_limit_works' => (bool) $can_set,
			'post_max_size'        => ini_get( 'post_max_size' ),
			'upload_max_filesize'  => ini_get( 'upload_max_filesize' ),
		),
		'checks' => array(
			'auth'                      => isset( $_SERVER['HTTP_X_WPU_KEY'] ) ? 'connection key' : 'application password',
			'member'                    => isset( $GLOBALS['wpu_bridge_member'] ) ? (string) $GLOBALS['wpu_bridge_member'] : '',
			'seo_plugin'                => wpu_bridge_seo_plugin(),
			'authorization_header_seen' => ! empty( $_SERVER['HTTP_AUTHORIZATION'] ),
			'app_passwords_available'   => function_exists( 'wp_is_application_passwords_available' ) ? wp_is_application_passwords_available() : null,
			'wp_debug_log'              => defined( 'WP_DEBUG_LOG' ) ? WP_DEBUG_LOG : false,
			'content_writable'          => is_writable( WP_CONTENT_DIR ),
			'mu_plugins_dir'            => is_dir( WPMU_PLUGIN_DIR ),
			'security_plugins'          => $security,
			'object_cache'              => (bool) wp_using_ext_object_cache(),
		),
		'stack'  => array(
			'theme'          => get_stylesheet(),
			'active_plugins' => count( $active ),
			'elementor'      => defined( 'ELEMENTOR_VERSION' ) ? ELEMENTOR_VERSION : null,
			'woocommerce'    => defined( 'WC_VERSION' ) ? WC_VERSION : null,
		),
	) );
}

/* -------------------------------------------------------------------------
 * /run - execute a toolkit script.
 *
 * The payload is base64 so that mod_security rules matching "<?php" or "eval"
 * in a request body do not eat it; that is a transport concern, not a security
 * measure, and nothing here relies on it being opaque.
 * ---------------------------------------------------------------------- */

function wpu_bridge_run( WP_REST_Request $request ) {

	$b64 = (string) $request->get_param( 'code_b64' );
	if ( '' === $b64 ) {
		return new WP_Error( 'wpu_no_code', 'code_b64 is required.', array( 'status' => 400 ) );
	}

	$code = base64_decode( $b64, true );
	if ( false === $code ) {
		return new WP_Error( 'wpu_bad_b64', 'code_b64 did not decode.', array( 'status' => 400 ) );
	}

	// Parse-check before running. A syntax error is reported cleanly here rather
	// than as an uncatchable fatal that takes the whole response down with it.
	$parse = wpu_bridge_lint( $code );
	if ( true !== $parse ) {
		return rest_ensure_response( array(
			'ok'         => false,
			'script'     => (string) $request->get_param( 'filename' ),
			'output'     => '',
			'fatal'      => 'PHP parse error: ' . $parse,
			'elapsed_ms' => 0,
			'peak_mb'    => '0.0',
		) );
	}

	$name = (string) $request->get_param( 'filename' );
	$name = $name ? preg_replace( '/[^A-Za-z0-9._-]/', '', $name ) : '';
	if ( '' === $name ) {
		$name = 'wpu-script.php';
	}

	$args = array_values( array_map( 'strval', (array) $request->get_param( 'args' ) ) );

	wpu_bridge_record( $name, strlen( $code ), $args );

	// Match what the local wrapper does, so scripts behave identically.
	@set_time_limit( 0 );
	@ini_set( 'memory_limit', '512M' );
	@ini_set( 'display_errors', '1' ); // wpsec:ignore - admin-only route, output is captured into the JSON reply
	if ( ! defined( 'DONOTCACHEPAGE' ) ) {
		define( 'DONOTCACHEPAGE', true );
	}
	if ( ! defined( 'DONOTCACHEOBJECT' ) ) {
		define( 'DONOTCACHEOBJECT', true );
	}
	if ( ! defined( 'DONOTMINIFY' ) ) {
		define( 'DONOTMINIFY', true );
	}

	/*
	 * Write the script somewhere the web server does not serve. get_temp_dir() can
	 * resolve inside wp-content (a host may set WP_TEMP_DIR to uploads), and a copy
	 * left there by a request the host killed mid-run is a public, executable PHP
	 * file - found on a live site on 2026-09-27. The guard line makes any stray copy
	 * inert if opened directly, and stale copies are swept on every run.
	 */
	$dir = wpu_bridge_private_dir( 'tmp' );
	wpu_bridge_sweep_stale( $dir );
	$file = trailingslashit( $dir ) . 'wpu-' . wp_generate_password( 12, false ) . '.php';
	$code = "<?php defined( 'ABSPATH' ) || exit; ?>" . $code;

	if ( false === file_put_contents( $file, $code ) ) {
		return new WP_Error( 'wpu_tmp', 'Could not write a temporary file to ' . $dir, array( 'status' => 500 ) );
	}

	$start = microtime( true );

	/*
	 * Toolkit scripts routinely end with exit() - every dry run does. exit()
	 * from inside a REST callback kills the request before a response is built,
	 * which would look exactly like a crash. So the shutdown handler owns the
	 * response whenever this function does not finish normally: it covers both
	 * a deliberate exit() and a real fatal, and either way the caller gets the
	 * script's output back instead of a white screen.
	 */
	$GLOBALS['wpu_bridge_running'] = array(
		'file'  => $file,
		'start' => $start,
		'name'  => $name,
	);
	register_shutdown_function( 'wpu_bridge_shutdown' );

	// $argv is a local here on purpose: an included file inherits the including
	// scope, so the script sees $argv exactly as it would on the command line.
	$argv = array_merge( array( $name ), $args );
	$argc = count( $argv );
	unset( $argc ); // declared for parity; scripts read $argv

	/*
	 * The buffer needs a capturing callback, not a plain ob_start().
	 *
	 * WordPress registers shutdown_action_hook() at bootstrap, and that calls
	 * wp_ob_end_flush_all() - so on any exit() the script's output is flushed
	 * straight to the client BEFORE a shutdown function registered here ever
	 * runs. A plain ob_start() therefore loses the output entirely: it arrives
	 * as loose text sitting outside the JSON, and the response reports an empty
	 * result. Swallowing the flush in a callback keeps it ours either way.
	 */
	$GLOBALS['wpu_bridge_out'] = '';
	$ob_level                   = ob_get_level();
	ob_start( 'wpu_bridge_ob_capture' );

	$fatal = null;
	try {
		include $file;
	} catch ( \Throwable $e ) {
		// Catches undefined functions, type errors and ParseError from the
		// include - nearly every fatal a toolkit script can raise - so the
		// response is built normally instead of being rescued at shutdown.
		$fatal = sprintf(
			'%s: %s in %s on line %d',
			get_class( $e ),
			$e->getMessage(),
			$e->getFile(),
			$e->getLine()
		);
	}

	/*
	 * Close down to the level we started at, always with ob_end_flush() so the
	 * capture callback is the single source of truth.
	 *
	 * Do NOT use ob_get_clean() here: it invokes the callback AND returns the
	 * buffer, so combining the two duplicated every script's entire output.
	 * Any buffer the script opened itself flushes inward into ours on the way.
	 */
	while ( ob_get_level() > $ob_level ) {
		ob_end_flush();
	}
	$output = $GLOBALS['wpu_bridge_out'];

	unset( $GLOBALS['wpu_bridge_running'], $GLOBALS['wpu_bridge_out'] );
	@unlink( $file );

	return rest_ensure_response( wpu_bridge_result( null === $fatal, $output, $fatal, $start, $name ) );
}

/** Absorb script output and emit nothing: the response body is JSON we build. */
function wpu_bridge_ob_capture( $chunk ) {
	if ( isset( $GLOBALS['wpu_bridge_out'] ) ) {
		$GLOBALS['wpu_bridge_out'] .= $chunk;
	}
	return '';
}

function wpu_bridge_shutdown() {

	if ( empty( $GLOBALS['wpu_bridge_running'] ) ) {
		return; // handler completed normally; nothing to rescue
	}

	$ctx = $GLOBALS['wpu_bridge_running'];
	unset( $GLOBALS['wpu_bridge_running'] );

	// Same rule as the normal path: flush through the callback, then read the
	// one place the output lives. By the time WordPress reaches here it has
	// usually flushed already, so this loop is normally a no-op.
	while ( ob_get_level() > 0 ) {
		ob_end_flush();
	}
	$output = isset( $GLOBALS['wpu_bridge_out'] ) ? $GLOBALS['wpu_bridge_out'] : '';
	unset( $GLOBALS['wpu_bridge_out'] );

	@unlink( $ctx['file'] );

	$fatal = null;
	$e     = error_get_last();
	if ( $e && in_array( $e['type'], array( E_ERROR, E_PARSE, E_COMPILE_ERROR, E_CORE_ERROR, E_USER_ERROR ), true ) ) {
		$fatal = sprintf( '%s in %s on line %d', $e['message'], $e['file'], $e['line'] );
	}

	if ( ! headers_sent() ) {
		status_header( 200 );
		header( 'Content-Type: application/json; charset=utf-8' );
	}

	echo wpu_bridge_json( wpu_bridge_result( null === $fatal, $output, $fatal, $ctx['start'], $ctx['name'] ) );
}

function wpu_bridge_result( $ok, $output, $fatal, $start, $name ) {
	return array(
		'ok'         => (bool) $ok,
		'script'     => $name,
		'output'     => (string) $output,
		'fatal'      => $fatal,
		'elapsed_ms' => (int) round( ( microtime( true ) - $start ) * 1000 ),
		// A string, not a float: json_encode renders 22.2 as 22.199999999999999
		// under the default serialize_precision, which looks like a bug.
		'peak_mb'    => number_format( memory_get_peak_usage() / 1048576, 1, '.', '' ),
	);
}

/** Script output is not guaranteed to be valid UTF-8; do not let that swallow the response. */
function wpu_bridge_json( $data ) {
	$flags = 0;
	if ( defined( 'JSON_INVALID_UTF8_SUBSTITUTE' ) ) {
		$flags |= JSON_INVALID_UTF8_SUBSTITUTE;
	}
	$json = wp_json_encode( $data, $flags );
	if ( false === $json ) {
		$json = wp_json_encode( array(
			'ok'     => false,
			'output' => '',
			'fatal'  => 'Response could not be encoded as JSON (likely invalid UTF-8 in script output).',
		) );
	}
	return $json;
}

/* -------------------------------------------------------------------------
 * /log - the fatal-error log, which is where the real answer usually is.
 * ---------------------------------------------------------------------- */

function wpu_bridge_log( WP_REST_Request $request ) {

	$lines = (int) $request->get_param( 'lines' );
	$lines = $lines > 0 ? min( $lines, 2000 ) : 200;

	$candidates = array();
	if ( defined( 'WP_DEBUG_LOG' ) && is_string( WP_DEBUG_LOG ) ) {
		$candidates[] = WP_DEBUG_LOG;
	}
	$candidates[] = WP_CONTENT_DIR . '/debug.log';
	$candidates[] = WP_CONTENT_DIR . '/uploads/debug.log';
	$candidates[] = ABSPATH . 'error_log';
	$candidates[] = ABSPATH . 'wp-admin/error_log';
	$ini = ini_get( 'error_log' );
	if ( $ini ) {
		$candidates[] = $ini;
	}
	$candidates = array_values( array_unique( array_filter( $candidates ) ) );

	foreach ( $candidates as $path ) {
		if ( ! @is_readable( $path ) ) {
			continue;
		}
		$all = @file( $path, FILE_IGNORE_NEW_LINES );
		if ( false === $all ) {
			continue;
		}
		$tail = array_slice( $all, -$lines );
		return rest_ensure_response( array(
			'ok'    => true,
			'path'  => $path,
			'size'  => filesize( $path ),
			'lines' => count( $tail ),
			'log'   => implode( "\n", $tail ),
		) );
	}

	return rest_ensure_response( array(
		'ok'      => false,
		'log'     => '',
		'checked' => $candidates,
		'note'    => 'No readable log found. Set WP_DEBUG_LOG in wp-config.php.',
	) );
}

/* -------------------------------------------------------------------------
 * /file - read and write inside wp-content only.
 *
 * Writing an mu-plugin through /run means escaping a PHP file inside a PHP
 * string, which is where mistakes live. This sends the bytes as bytes.
 * ---------------------------------------------------------------------- */

function wpu_bridge_file( WP_REST_Request $request ) {

	$rel = (string) $request->get_param( 'path' );
	if ( '' === $rel ) {
		return new WP_Error( 'wpu_no_path', 'path is required, relative to wp-content.', array( 'status' => 400 ) );
	}

	$rel = str_replace( '\\', '/', $rel );
	if ( false !== strpos( $rel, "\0" ) || preg_match( '#(^|/)\.\.(/|$)#', $rel ) ) {
		return new WP_Error( 'wpu_traversal', 'Path traversal refused.', array( 'status' => 400 ) );
	}

	$base = wp_normalize_path( realpath( WP_CONTENT_DIR ) );
	$full = wp_normalize_path( trailingslashit( WP_CONTENT_DIR ) . ltrim( $rel, '/' ) );

	// Confirm containment against the nearest folder that exists, since the file -
	// and on a fresh site even mu-plugins/ - may not exist yet. ".." was refused above,
	// so walking up can only reach ancestors of the requested path.
	$probe = dirname( $full );
	while ( ! is_dir( $probe ) && strlen( $probe ) > strlen( $base ) ) {
		$probe = dirname( $probe );
	}
	$parent = realpath( $probe );
	if ( ! $parent || 0 !== strpos( trailingslashit( wp_normalize_path( $parent ) ), trailingslashit( $base ) ) ) {
		return new WP_Error( 'wpu_outside', 'Refusing to touch anything outside wp-content.', array( 'status' => 400 ) );
	}

	// The parent check above does not cover a symlink AS the last segment (common on
	// managed hosts), which could point at wp-config.php. Refuse links; re-check real files.
	if ( is_link( $full ) ) {
		return new WP_Error( 'wpu_outside', 'Refusing to follow a symlink.', array( 'status' => 400 ) );
	}
	if ( file_exists( $full ) ) {
		$real = realpath( $full );
		if ( ! $real || 0 !== strpos( wp_normalize_path( $real ), trailingslashit( $base ) ) ) {
			return new WP_Error( 'wpu_outside', 'Refusing to touch anything outside wp-content.', array( 'status' => 400 ) );
		}
	}

	$is_php = (bool) preg_match( '/\.php$/i', $full );

	if ( 'GET' === $request->get_method() ) {
		if ( ! @is_readable( $full ) ) {
			return new WP_Error( 'wpu_missing', 'Not readable: ' . $rel, array( 'status' => 404 ) );
		}
		return rest_ensure_response( array(
			'ok'          => true,
			'path'        => $rel,
			'bytes'       => filesize( $full ),
			'modified'    => gmdate( 'c', filemtime( $full ) ),
			'content_b64' => base64_encode( (string) file_get_contents( $full ) ),
		) );
	}

	$b64 = (string) $request->get_param( 'content_b64' );
	if ( '' === $b64 ) {
		return new WP_Error( 'wpu_no_content', 'content_b64 is required to write.', array( 'status' => 400 ) );
	}
	$content = base64_decode( $b64, true );
	if ( false === $content ) {
		return new WP_Error( 'wpu_bad_b64', 'content_b64 did not decode.', array( 'status' => 400 ) );
	}

	$bom_stripped = false;

	if ( $is_php ) {
		/*
		 * A UTF-8 BOM before "<?php" is emitted as body bytes on every single
		 * request, which produces "headers already sent" and breaks redirects
		 * and cookies site-wide. It is never intentional, and it is easy to
		 * introduce by accident - Windows PowerShell's Set-Content -Encoding
		 * utf8 writes one every time. Strip it and say so.
		 */
		if ( 0 === strncmp( $content, "\xEF\xBB\xBF", 3 ) ) {
			$content      = substr( $content, 3 );
			$bom_stripped = true;
		}

		// A PHP file that will not parse takes the whole site down - and if it is
		// an mu-plugin, it takes this bridge down with it and there is no way
		// back in. Check before writing, never after.
		$check = wpu_bridge_lint( $content );
		if ( true !== $check ) {
			return new WP_Error( 'wpu_parse', 'Refused: PHP does not parse - ' . $check, array( 'status' => 400 ) );
		}
	}

	if ( ! wp_mkdir_p( dirname( $full ) ) ) {
		return new WP_Error( 'wpu_mkdir', 'Could not create ' . dirname( $rel ), array( 'status' => 500 ) );
	}

	// Keep the previous version outside the web root: a .bak beside the file is
	// downloadable as plain source code.
	$backup = null;
	if ( file_exists( $full ) ) {
		$bdir   = wpu_bridge_private_dir( 'backups' );
		$backup = trailingslashit( $bdir ) . str_replace( '/', '__', $rel ) . '.wpu-' . gmdate( 'Ymd-His' ) . '-' . wp_generate_password( 8, false ) . '.bak';
		@copy( $full, $backup );
	}

	$written = file_put_contents( $full, $content );
	if ( false === $written ) {
		return new WP_Error( 'wpu_write', 'Write failed - check permissions on ' . dirname( $rel ), array( 'status' => 500 ) );
	}

	wpu_bridge_record( 'file:' . $rel, $written, array() );

	return rest_ensure_response( array(
		'ok'           => true,
		'path'         => $rel,
		'bytes'        => $written,
		'backup'       => $backup ? basename( $backup ) : null,
		'linted'       => $is_php,
		'bom_stripped' => $bom_stripped,
	) );
}

/**
 * Parse-check PHP source without shelling out - exec() is disabled on most
 * shared hosting, so `php -l` is not available.
 */
function wpu_bridge_lint( $source ) {
	if ( ! function_exists( 'token_get_all' ) || ! defined( 'TOKEN_PARSE' ) ) {
		return true; // cannot check; do not block
	}
	try {
		$tokens = @token_get_all( $source, TOKEN_PARSE );
		unset( $tokens );
		return true;
	} catch ( \ParseError $e ) {
		return $e->getMessage() . ' on line ' . $e->getLine();
	} catch ( \Throwable $e ) {
		return $e->getMessage();
	}
}

/* -------------------------------------------------------------------------
 * Audit trail - last 50 calls, so the site owner can see what was done.
 * ---------------------------------------------------------------------- */

/**
 * A private working folder for SEO/file backups and /run temp scripts.
 *
 * 1. <dir above ABSPATH>/wpu-bridge/<sub> - but only if that is NOT inside the web root
 *    (Bedrock's web/wp and installs in a subfolder put it in a served folder).
 * 2. The system temp dir, only in a folder this PHP user created and owns, mode 0700 - on shared
 *    hosting another account could pre-create a predictable /tmp folder and read or swap files.
 * 3. wp-content/uploads/wpu-bridge-<random>/<sub>, with a deny-all .htaccess and an index.php.
 * Every folder gets the deny files too, in case the web-root test was wrong.
 */
function wpu_bridge_private_dir( $sub ) {
	$sub     = sanitize_key( $sub );
	$docroot = isset( $_SERVER['DOCUMENT_ROOT'] ) ? wp_normalize_path( (string) realpath( sanitize_text_field( wp_unslash( $_SERVER['DOCUMENT_ROOT'] ) ) ) ) : '';
	$uid     = function_exists( 'getmyuid' ) ? getmyuid() : null;

	$above = dirname( rtrim( ABSPATH, '/\\' ) );
	$above_real = wp_normalize_path( (string) realpath( $above ) );
	if ( $above_real && ( '' === $docroot || 0 !== strpos( trailingslashit( $above_real ), trailingslashit( $docroot ) ) ) ) {
		$dir = $above . '/wpu-bridge/' . $sub;
		if ( wpu_bridge_prepare_dir( $dir ) ) {
			return $dir;
		}
	}

	$token = get_option( 'wpu_bridge_dir_token' );
	if ( ! $token || ! preg_match( '/^[a-z0-9]{16}$/', $token ) ) {
		$token = strtolower( wp_generate_password( 16, false ) );
		update_option( 'wpu_bridge_dir_token', $token, false );
	}

	$tmp = rtrim( sys_get_temp_dir(), '/\\' ) . '/wpu-bridge-' . $token;
	if ( ( is_dir( $tmp ) || @mkdir( $tmp, 0700 ) ) && ! is_link( $tmp ) && ( null === $uid || false === $uid || @fileowner( $tmp ) === $uid ) ) {
		@chmod( $tmp, 0700 );
		if ( wpu_bridge_prepare_dir( $tmp . '/' . $sub ) ) {
			return $tmp . '/' . $sub;
		}
	}

	$up  = wp_upload_dir( null, false );
	$dir = trailingslashit( $up['basedir'] ) . 'wpu-bridge-' . $token;
	if ( wpu_bridge_prepare_dir( $dir ) && wpu_bridge_prepare_dir( $dir . '/' . $sub ) ) {
		return $dir . '/' . $sub;
	}
	return untrailingslashit( get_temp_dir() );
}

/** Create a folder if needed and drop deny-all files in it. */
function wpu_bridge_prepare_dir( $dir ) {
	if ( ! ( is_dir( $dir ) || @wp_mkdir_p( $dir ) ) || ! is_writable( $dir ) ) {
		return false;
	}
	if ( ! file_exists( $dir . '/.htaccess' ) ) {
		@file_put_contents( $dir . '/.htaccess', "Require all denied\nDeny from all\n" );
	}
	if ( ! file_exists( $dir . '/index.php' ) ) {
		@file_put_contents( $dir . '/index.php', "<?php // Silence is golden.\n" );
	}
	return true;
}

/** Remove bridge temp scripts older than an hour (left behind when a host kills a request). */
function wpu_bridge_sweep_stale( $dir ) {
	foreach ( (array) glob( trailingslashit( $dir ) . 'wpu-*.php' ) as $f ) {
		if ( is_file( $f ) && filemtime( $f ) < time() - HOUR_IN_SECONDS ) {
			@unlink( $f );
		}
	}
}

function wpu_bridge_record( $what, $bytes, $args ) {
	$entries   = (array) get_option( 'wpu_bridge_audit', array() );
	$entries[] = array(
		'at'    => gmdate( 'c' ),
		'user'  => wp_get_current_user()->user_login,
		'member' => isset( $GLOBALS['wpu_bridge_member'] ) ? (string) $GLOBALS['wpu_bridge_member'] : '',
		'ip'    => isset( $_SERVER['REMOTE_ADDR'] ) ? sanitize_text_field( wp_unslash( $_SERVER['REMOTE_ADDR'] ) ) : '',
		'what'  => (string) $what,
		'bytes' => (int) $bytes,
		'args'  => $args,
	);
	update_option( 'wpu_bridge_audit', array_slice( $entries, -50 ), false );
}

function wpu_bridge_audit() {
	return rest_ensure_response( array(
		'ok'      => true,
		'entries' => array_values( (array) get_option( 'wpu_bridge_audit', array() ) ),
	) );
}

/* -------------------------------------------------------------------------
 * /media - add a file to the Media Library through WordPress's own upload
 * handling, so thumbnails exist and host scanners leave it alone (files written
 * into uploads/ by a script were deleted by a scanner within minutes on one
 * host). Same name + same size already in the library is reused, not duplicated.
 *
 * /template - import an Elementor template export through Elementor's own
 * importer, exactly as Templates > Saved Templates > Import does.
 *
 * Both from WP Site Build Bridge 1.0.0, unchanged apart from the prefix.
 * ---------------------------------------------------------------------- */

function wpu_bridge_media( WP_REST_Request $request ) {

	$name = sanitize_file_name( (string) $request->get_param( 'filename' ) );
	$b64  = (string) $request->get_param( 'content_b64' );
	if ( '' === $name || '' === $b64 ) {
		return new WP_Error( 'wpu_media_args', 'filename and content_b64 are required.', array( 'status' => 400 ) );
	}
	$bytes = base64_decode( $b64, true );
	if ( false === $bytes ) {
		return new WP_Error( 'wpu_bad_b64', 'content_b64 did not decode.', array( 'status' => 400 ) );
	}
	if ( strlen( $bytes ) > 25 * MB_IN_BYTES ) {
		return new WP_Error( 'wpu_media_size', 'File is larger than 25 MB.', array( 'status' => 400 ) );
	}

	// Re-run safety: same filename + same size already in the library -> reuse it.
	$existing = get_posts( array(
		'post_type'      => 'attachment',
		'post_status'    => 'inherit',
		'posts_per_page' => 20,
		'meta_query'     => array( array( 'key' => '_wp_attached_file', 'value' => pathinfo( $name, PATHINFO_FILENAME ), 'compare' => 'LIKE' ) ),
	) );
	foreach ( $existing as $att ) {
		$path = get_attached_file( $att->ID );
		if ( $path && basename( $path ) === $name && @filesize( $path ) === strlen( $bytes ) ) {
			return rest_ensure_response( array( 'ok' => true, 'reused' => true, 'id' => $att->ID, 'url' => wp_get_attachment_url( $att->ID ), 'mime' => $att->post_mime_type, 'bytes' => strlen( $bytes ) ) );
		}
	}

	require_once ABSPATH . 'wp-admin/includes/file.php';
	require_once ABSPATH . 'wp-admin/includes/media.php';
	require_once ABSPATH . 'wp-admin/includes/image.php';

	$tmp = wp_tempnam( $name );
	if ( ! $tmp || false === file_put_contents( $tmp, $bytes ) ) {
		return new WP_Error( 'wpu_tmp', 'Could not write a temporary file.', array( 'status' => 500 ) );
	}

	$file  = array( 'name' => $name, 'tmp_name' => $tmp, 'size' => strlen( $bytes ), 'error' => 0 );
	$moved = wp_handle_sideload( $file, array( 'test_form' => false ) );
	if ( ! empty( $moved['error'] ) ) {
		@unlink( $tmp );
		// Most common cause: SVG / WEBP / font types not allowed by this site's upload mimes.
		return new WP_Error( 'wpu_upload', 'Upload refused: ' . $moved['error'], array( 'status' => 400 ) );
	}

	$id = wp_insert_attachment( array(
		'post_title'     => sanitize_text_field( pathinfo( $name, PATHINFO_FILENAME ) ),
		'post_mime_type' => $moved['type'],
		'post_status'    => 'inherit',
	), $moved['file'] );
	if ( is_wp_error( $id ) ) {
		return $id;
	}
	wp_update_attachment_metadata( $id, wp_generate_attachment_metadata( $id, $moved['file'] ) );

	$alt = sanitize_text_field( (string) $request->get_param( 'alt' ) );
	if ( '' !== $alt ) {
		update_post_meta( $id, '_wp_attachment_image_alt', $alt );
	}

	wpu_bridge_record( 'media:' . $name, strlen( $bytes ), array() );

	return rest_ensure_response( array( 'ok' => true, 'reused' => false, 'id' => $id, 'url' => wp_get_attachment_url( $id ), 'mime' => $moved['type'], 'bytes' => strlen( $bytes ) ) );
}

function wpu_bridge_template( WP_REST_Request $request ) {

	if ( ! class_exists( '\Elementor\Plugin' ) ) {
		return new WP_Error( 'wpu_no_elementor', 'Elementor is not active on this site.', array( 'status' => 400 ) );
	}

	$name = sanitize_file_name( (string) $request->get_param( 'filename' ) );
	$b64  = (string) $request->get_param( 'json_b64' );
	if ( '' === $b64 || false === base64_decode( $b64, true ) ) {
		return new WP_Error( 'wpu_bad_b64', 'json_b64 is required and must decode.', array( 'status' => 400 ) );
	}
	if ( '' === $name ) {
		$name = 'template.json';
	}

	$result = \Elementor\Plugin::$instance->templates_manager->import_template( array(
		'fileName' => $name,
		'fileData' => $b64,
	) );

	if ( is_wp_error( $result ) ) {
		return new WP_Error( 'wpu_import', 'Elementor refused the import: ' . $result->get_error_message(), array( 'status' => 400 ) );
	}

	$out = array();
	foreach ( (array) $result as $t ) {
		$t     = (array) $t;
		$out[] = array(
			'id'    => (int) ( $t['template_id'] ?? 0 ),
			'title' => (string) ( $t['title'] ?? '' ),
			'type'  => (string) ( $t['type'] ?? '' ),
		);
	}

	wpu_bridge_record( 'template:' . $name, strlen( $b64 ), array() );

	return rest_ensure_response( array( 'ok' => true, 'templates' => $out ) );
}

/* -------------------------------------------------------------------------
 * /seo - read and write per-page SEO fields for whichever SEO plugin the site
 * runs, with a backup before every write and a rollback route.
 *
 * Field names are ours; the bridge maps them to the plugin's own meta keys, so
 * the toolkit never has to know them:
 *
 *   title, description, focus_keyword, canonical, noindex (bool), schema
 *
 * schema is a JSON-LD object (or list of them). It is stored in the _wpu_schema
 * post meta and printed by the separate, permanent mu-plugin wpu-seo-schema.php
 * - NOT by this bridge, which expires. Install that mu-plugin once per site.
 *
 * Writes are only ever data. No field is evaluated, and Elementor content is
 * never touched here.
 * ---------------------------------------------------------------------- */

/** 'rankmath' | 'yoast' | 'aioseo' | 'seopress' | 'none' */
function wpu_bridge_seo_plugin() {
	if ( class_exists( 'RankMath' ) || defined( 'RANK_MATH_VERSION' ) ) {
		return 'rankmath';
	}
	if ( defined( 'WPSEO_VERSION' ) ) {
		return 'yoast';
	}
	if ( defined( 'AIOSEO_VERSION' ) ) {
		return 'aioseo';
	}
	if ( defined( 'SEOPRESS_VERSION' ) ) {
		return 'seopress';
	}
	return 'none';
}

/** Our field name => the active plugin's meta key. Empty for unsupported plugins. */
function wpu_bridge_seo_map( $plugin ) {
	if ( 'rankmath' === $plugin ) {
		return array(
			'title'         => 'rank_math_title',
			'description'   => 'rank_math_description',
			'focus_keyword' => 'rank_math_focus_keyword',
			'canonical'     => 'rank_math_canonical_url',
			'noindex'       => 'rank_math_robots',
		);
	}
	if ( 'yoast' === $plugin ) {
		return array(
			'title'         => '_yoast_wpseo_title',
			'description'   => '_yoast_wpseo_metadesc',
			'focus_keyword' => '_yoast_wpseo_focuskw',
			'canonical'     => '_yoast_wpseo_canonical',
			'noindex'       => '_yoast_wpseo_meta-robots-noindex',
		);
	}
	return array();
}

function wpu_bridge_seo_read( $post_id, $plugin ) {
	$map = wpu_bridge_seo_map( $plugin );
	$out = array();
	foreach ( $map as $field => $key ) {
		$val = get_post_meta( $post_id, $key, true );
		if ( 'noindex' === $field ) {
			if ( 'rankmath' === $plugin ) {
				$out[ $field ] = is_array( $val ) && in_array( 'noindex', $val, true );
			} else {
				$out[ $field ] = '1' === (string) $val;
			}
			continue;
		}
		$out[ $field ] = '' === (string) $val ? null : (string) $val;
	}
	$schema          = get_post_meta( $post_id, '_wpu_schema', true );
	$out['schema']   = '' === $schema ? null : json_decode( (string) $schema, true );
	return $out;
}

function wpu_bridge_seo( WP_REST_Request $request ) {
	$plugin = wpu_bridge_seo_plugin();

	if ( 'GET' === $request->get_method() ) {
		$types = array_filter( array_map( 'sanitize_key', explode( ',', (string) $request->get_param( 'types' ) ) ) );
		if ( ! $types ) {
			$types = array( 'page', 'post' );
		}
		$status = 'any' === $request->get_param( 'status' ) ? array( 'publish', 'draft', 'pending', 'future', 'private' ) : array( 'publish' );
		$ids    = get_posts( array(
			'post_type'      => $types,
			'post_status'    => $status,
			'posts_per_page' => 500,
			'fields'         => 'ids',
			'orderby'        => 'ID',
			'order'          => 'ASC',
		) );
		$rows = array();
		foreach ( $ids as $id ) {
			$rows[] = array(
				'id'      => (int) $id,
				'type'    => get_post_type( $id ),
				'status'  => get_post_status( $id ),
				'title'   => get_the_title( $id ),
				'url'     => get_permalink( $id ),
				'builder' => get_post_meta( $id, '_elementor_edit_mode', true ) ? 'elementor' : 'wordpress',
				'seo'     => wpu_bridge_seo_read( $id, $plugin ),
			);
		}
		return rest_ensure_response( array(
			'ok'         => true,
			'seo_plugin' => $plugin,
			'writable'   => (bool) wpu_bridge_seo_map( $plugin ),
			'pages'      => $rows,
		) );
	}

	// POST: { "items": [ { "id": 12, "title": "...", "description": "...", ... } ], "apply": true }
	$items = $request->get_param( 'items' );
	$apply = (bool) $request->get_param( 'apply' );
	if ( ! is_array( $items ) || ! $items ) {
		return new WP_Error( 'wpu_seo_items', 'items must be a non-empty list.', array( 'status' => 400 ) );
	}
	if ( count( $items ) > 200 ) {
		return new WP_Error( 'wpu_seo_many', 'At most 200 items per call - split the job.', array( 'status' => 400 ) );
	}
	$map = wpu_bridge_seo_map( $plugin );
	if ( ! $map ) {
		return new WP_Error(
			'wpu_seo_plugin',
			'No supported SEO plugin is active (found: ' . $plugin . '). Install Rank Math or Yoast first.',
			array( 'status' => 400 )
		);
	}

	$backup  = array( 'plugin' => $plugin, 'at' => gmdate( 'c' ), 'items' => array() );
	$results = array();

	foreach ( $items as $item ) {
		if ( ! is_array( $item ) ) {
			continue;
		}
		$id   = isset( $item['id'] ) ? absint( $item['id'] ) : 0;
		$post = $id ? get_post( $id ) : null;
		if ( ! $post ) {
			$results[] = array( 'id' => $id, 'ok' => false, 'error' => 'no such post' );
			continue;
		}

		$before  = wpu_bridge_seo_read( $id, $plugin );
		$changes = array();
		foreach ( array( 'title', 'description', 'focus_keyword', 'canonical', 'noindex', 'schema' ) as $field ) {
			if ( ! array_key_exists( $field, $item ) ) {
				continue;
			}
			$new = $item[ $field ];
			if ( 'noindex' === $field ) {
				$new = (bool) $new;
			} elseif ( 'canonical' === $field ) {
				$new = null === $new || '' === $new ? null : esc_url_raw( (string) $new );
			} elseif ( 'schema' === $field ) {
				if ( null !== $new && ! is_array( $new ) ) {
					$results[] = array( 'id' => $id, 'ok' => false, 'error' => 'schema must be a JSON object or list' );
					continue 2;
				}
			} else {
				$new = null === $new ? null : sanitize_text_field( (string) $new );
			}
			if ( $before[ $field ] !== $new ) {
				$changes[ $field ] = array( 'from' => $before[ $field ], 'to' => $new );
			}
		}

		// An empty array would encode as [] - send {} so clients can always treat it as a map.
		$results[] = array( 'id' => $id, 'ok' => true, 'url' => get_permalink( $id ), 'changes' => $changes ? $changes : new stdClass() );
		if ( ! $apply || ! $changes ) {
			continue;
		}

		$backup['items'][ $id ] = $before;
		foreach ( $changes as $field => $c ) {
			wpu_bridge_seo_write_field( $id, $plugin, $field, $c['to'] );
		}
		wpu_bridge_seo_refresh( $id, $plugin );
	}

	$ref = null;
	if ( $apply && $backup['items'] ) {
		$ref  = 'seo-' . gmdate( 'Ymd-His' ) . '-' . wp_generate_password( 6, false );
		$file = trailingslashit( wpu_bridge_private_dir( 'backups' ) ) . $ref . '.json';
		file_put_contents( $file, wp_json_encode( $backup ) );
		wpu_bridge_record( 'seo:write', count( $backup['items'] ), array( $ref ) );
	}

	return rest_ensure_response( array(
		'ok'         => true,
		'applied'    => $apply,
		'seo_plugin' => $plugin,
		'backup_ref' => $ref,
		'results'    => $results,
	) );
}

function wpu_bridge_seo_write_field( $id, $plugin, $field, $value ) {
	if ( 'schema' === $field ) {
		if ( null === $value ) {
			delete_post_meta( $id, '_wpu_schema' );
		} else {
			update_post_meta( $id, '_wpu_schema', wp_slash( wp_json_encode( $value ) ) );
		}
		return;
	}

	$map = wpu_bridge_seo_map( $plugin );
	$key = $map[ $field ];

	if ( 'noindex' === $field ) {
		if ( 'rankmath' === $plugin ) {
			$robots = get_post_meta( $id, $key, true );
			$robots = is_array( $robots ) ? array_values( array_diff( $robots, array( 'noindex', 'index' ) ) ) : array();
			$robots[] = $value ? 'noindex' : 'index';
			update_post_meta( $id, $key, $robots );
		} elseif ( $value ) {
			update_post_meta( $id, $key, '1' );
		} else {
			delete_post_meta( $id, $key );
		}
		return;
	}

	if ( null === $value || '' === $value ) {
		delete_post_meta( $id, $key );
	} else {
		update_post_meta( $id, $key, wp_slash( $value ) );
	}
}

/**
 * Make the change visible. Yoast serves titles from its indexable table, so new
 * meta alone keeps serving the old title until that row is rebuilt (see
 * knowledge/GOTCHAS.md, "Yoast meta survives a rename"). Delete the row and let
 * Yoast rebuild it on the next view. Then clear page caches we know about.
 */
function wpu_bridge_seo_refresh( $id, $plugin ) {
	global $wpdb;
	if ( 'yoast' === $plugin ) {
		$table = $wpdb->prefix . 'yoast_indexable';
		// $table is built from $wpdb->prefix, never from input.
		$wpdb->query( $wpdb->prepare( "DELETE FROM {$table} WHERE object_id = %d AND object_type = 'post'", $id ) ); // phpcs:ignore WordPress.DB.PreparedSQL.InterpolatedNotPrepared
	}
	clean_post_cache( $id );
	do_action( 'litespeed_purge_post', $id );
	if ( function_exists( 'rocket_clean_post' ) ) {
		rocket_clean_post( $id );
	}
}

function wpu_bridge_seo_rollback( WP_REST_Request $request ) {
	$ref = (string) $request->get_param( 'ref' );
	if ( ! preg_match( '/^seo-\d{8}-\d{6}-[A-Za-z0-9]{6}$/', $ref ) ) {
		return new WP_Error( 'wpu_seo_ref', 'ref is not a backup reference this bridge made.', array( 'status' => 400 ) );
	}
	$file = trailingslashit( wpu_bridge_private_dir( 'backups' ) ) . $ref . '.json';
	if ( ! is_readable( $file ) ) {
		return new WP_Error( 'wpu_seo_missing', 'Backup not found: ' . $ref, array( 'status' => 404 ) );
	}
	$backup = json_decode( (string) file_get_contents( $file ), true );
	if ( ! is_array( $backup ) || empty( $backup['items'] ) ) {
		return new WP_Error( 'wpu_seo_bad', 'Backup is empty or unreadable.', array( 'status' => 500 ) );
	}
	$plugin = (string) $backup['plugin'];
	if ( wpu_bridge_seo_plugin() !== $plugin ) {
		return new WP_Error( 'wpu_seo_switched', 'The SEO plugin changed since this backup was made (' . $plugin . ').', array( 'status' => 409 ) );
	}
	$restored = array();
	foreach ( $backup['items'] as $id => $fields ) {
		$id = absint( $id );
		if ( ! get_post( $id ) ) {
			continue;
		}
		foreach ( (array) $fields as $field => $value ) {
			wpu_bridge_seo_write_field( $id, $plugin, $field, $value );
		}
		wpu_bridge_seo_refresh( $id, $plugin );
		$restored[] = $id;
	}
	wpu_bridge_record( 'seo:rollback', count( $restored ), array( $ref ) );
	return rest_ensure_response( array( 'ok' => true, 'ref' => $ref, 'restored' => $restored ) );
}

/* -------------------------------------------------------------------------
 * /posts - create or update blog posts as data.
 *
 * GET  ?search=&status=  lists posts (id, title, slug, status, date).
 * POST { "post": {...}, "update": false } creates or updates one post, matched
 *      by slug. An existing slug is only overwritten with "update": true.
 *
 * Status is draft by default. "future" needs a date. "publish" needs
 * "confirm_publish": true, which the toolkit only sends after a person has
 * approved the post in the session.
 *
 * content is HTML or block markup; it is passed through wp_kses_post, the
 * same filter WordPress applies to an editor's content.
 * ---------------------------------------------------------------------- */

function wpu_bridge_posts( WP_REST_Request $request ) {

	if ( 'GET' === $request->get_method() ) {
		$status = sanitize_key( (string) $request->get_param( 'status' ) );
		$q      = get_posts( array(
			'post_type'      => 'post',
			'post_status'    => $status ? $status : array( 'publish', 'draft', 'pending', 'future' ),
			's'              => sanitize_text_field( (string) $request->get_param( 'search' ) ),
			'posts_per_page' => 200,
		) );
		$rows   = array();
		foreach ( $q as $p ) {
			$rows[] = array(
				'id'     => $p->ID,
				'title'  => get_the_title( $p ),
				'slug'   => $p->post_name,
				'status' => $p->post_status,
				'date'   => $p->post_date_gmt,
				'url'    => get_permalink( $p ),
			);
		}
		return rest_ensure_response( array( 'ok' => true, 'posts' => $rows ) );
	}

	$in = $request->get_param( 'post' );
	if ( ! is_array( $in ) || empty( $in['title'] ) ) {
		return new WP_Error( 'wpu_post_args', 'post.title is required.', array( 'status' => 400 ) );
	}

	$slug   = sanitize_title( isset( $in['slug'] ) && '' !== $in['slug'] ? (string) $in['slug'] : (string) $in['title'] );
	$status = isset( $in['status'] ) ? sanitize_key( (string) $in['status'] ) : 'draft';
	if ( ! in_array( $status, array( 'draft', 'pending', 'future', 'publish' ), true ) ) {
		return new WP_Error( 'wpu_post_status', 'status must be draft, pending, future or publish.', array( 'status' => 400 ) );
	}
	if ( 'publish' === $status && true !== $request->get_param( 'confirm_publish' ) ) {
		return new WP_Error( 'wpu_post_confirm', 'Publishing needs confirm_publish: true (a person approved it).', array( 'status' => 400 ) );
	}

	$data = array(
		'post_type'    => 'post',
		'post_title'   => sanitize_text_field( (string) $in['title'] ),
		'post_name'    => $slug,
		'post_content' => isset( $in['content'] ) ? wp_kses_post( (string) $in['content'] ) : '',
		'post_excerpt' => isset( $in['excerpt'] ) ? sanitize_textarea_field( (string) $in['excerpt'] ) : '',
		'post_status'  => $status,
	);

	if ( 'future' === $status ) {
		$ts = isset( $in['date'] ) ? strtotime( (string) $in['date'] ) : false;
		if ( ! $ts || $ts <= time() ) {
			return new WP_Error( 'wpu_post_date', 'status future needs a date in the future (ISO 8601).', array( 'status' => 400 ) );
		}
		$data['post_date_gmt'] = gmdate( 'Y-m-d H:i:s', $ts );
		$data['post_date']     = get_date_from_gmt( $data['post_date_gmt'] );
	}

	if ( ! empty( $in['author'] ) ) {
		$author = get_user_by( 'login', sanitize_user( (string) $in['author'] ) );
		if ( ! $author || ! user_can( $author, 'edit_posts' ) ) {
			return new WP_Error( 'wpu_post_author', 'author is not a user who can write posts.', array( 'status' => 400 ) );
		}
		$data['post_author'] = $author->ID;
	}

	$existing = get_page_by_path( $slug, OBJECT, 'post' );
	if ( $existing ) {
		if ( true !== $request->get_param( 'update' ) ) {
			return new WP_Error( 'wpu_post_exists', 'A post with slug "' . $slug . '" exists (#' . $existing->ID . '). Send update: true to change it.', array( 'status' => 409 ) );
		}
		$data['ID'] = $existing->ID;
	}

	$id = $existing ? wp_update_post( wp_slash( $data ), true ) : wp_insert_post( wp_slash( $data ), true );
	if ( is_wp_error( $id ) ) {
		return $id;
	}

	foreach ( array( 'categories' => 'category', 'tags' => 'post_tag' ) as $field => $tax ) {
		if ( empty( $in[ $field ] ) || ! is_array( $in[ $field ] ) ) {
			continue;
		}
		$term_ids = array();
		foreach ( $in[ $field ] as $name ) {
			$name = sanitize_text_field( (string) $name );
			if ( '' === $name ) {
				continue;
			}
			$term = term_exists( $name, $tax );
			if ( ! $term ) {
				$term = wp_insert_term( $name, $tax );
			}
			if ( ! is_wp_error( $term ) ) {
				$term_ids[] = (int) ( is_array( $term ) ? $term['term_id'] : $term );
			}
		}
		wp_set_post_terms( $id, $term_ids, $tax, false );
	}

	if ( ! empty( $in['featured_media'] ) ) {
		$att = absint( $in['featured_media'] );
		if ( $att && 'attachment' === get_post_type( $att ) ) {
			set_post_thumbnail( $id, $att );
		}
	}

	wpu_bridge_record( ( $existing ? 'post:update:' : 'post:create:' ) . $slug, strlen( $data['post_content'] ), array( $status ) );

	return rest_ensure_response( array(
		'ok'      => true,
		'id'      => (int) $id,
		'created' => ! $existing,
		'status'  => get_post_status( $id ),
		'url'     => get_permalink( $id ),
		'preview' => get_preview_post_link( $id ),
	) );
}
