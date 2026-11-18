<?php
/**
 * Site tools: overview, health check, logs, the change list and undo.
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/** Which page builders and themes builders are active. */
function wpu_bt_builders() {
	$b = array( 'gutenberg' => true );
	$checks = array(
		'elementor'      => defined( 'ELEMENTOR_VERSION' ),
		'elementor_pro'  => defined( 'ELEMENTOR_PRO_VERSION' ),
		'divi'           => defined( 'ET_BUILDER_VERSION' ) || 'Divi' === get_template(),
		'bricks'         => defined( 'BRICKS_VERSION' ),
		'beaver_builder' => class_exists( 'FLBuilder' ),
		'breakdance'     => defined( '__BREAKDANCE_VERSION' ) || defined( 'BREAKDANCE_PLUGIN_URL' ),
		'oxygen'         => defined( 'CT_VERSION' ),
		'wpbakery'       => defined( 'WPB_VC_VERSION' ),
		'seedprod'       => defined( 'SEEDPROD_VERSION' ) || defined( 'SEEDPROD_PRO_VERSION' ),
		'kadence_blocks' => defined( 'KADENCE_BLOCKS_VERSION' ),
		'spectra'        => defined( 'UAGB_VER' ),
		'generateblocks' => defined( 'GENERATEBLOCKS_VERSION' ),
	);
	foreach ( $checks as $k => $on ) {
		if ( $on ) {
			$b[ $k ] = true;
		}
	}
	return array_keys( $b );
}

/** The builder a given post is made with. */
function wpu_bt_post_builder( $post_id ) {
	if ( 'builder' === get_post_meta( $post_id, '_elementor_edit_mode', true ) ) {
		return 'elementor';
	}
	$content = (string) get_post_field( 'post_content', $post_id );
	if ( 'on' === get_post_meta( $post_id, '_et_pb_use_builder', true ) || false !== strpos( $content, '<!-- wp:divi/' ) || 0 === strpos( ltrim( $content ), '[et_pb_section' ) ) {
		return 'divi';
	}
	if ( get_post_meta( $post_id, '_bricks_page_content_2', true ) ) {
		return 'bricks';
	}
	if ( get_post_meta( $post_id, '_fl_builder_enabled', true ) ) {
		return 'beaver_builder';
	}
	if ( get_post_meta( $post_id, '_breakdance_data', true ) ) {
		return 'breakdance';
	}
	if ( get_post_meta( $post_id, '_seedprod_page', true ) || ( 0 === strpos( ltrim( (string) get_post_field( 'post_content_filtered', $post_id ) ), '{' ) && false !== strpos( (string) get_post_field( 'post_content_filtered', $post_id ), '"document"' ) ) ) {
		return 'seedprod';
	}
	if ( function_exists( 'has_blocks' ) && has_blocks( $content ) ) {
		return 'gutenberg';
	}
	return '' === trim( $content ) ? 'empty' : 'classic';
}

wpu_bt_define_tool( 'site_overview', array(
	'title'       => 'Site overview',
	'description' => 'Versions, theme, page builders, active plugins (with available updates), post types and which tools apply. Call this first.',
	'cap'         => 'manage_options',
	'run'         => function () {
		global $wp_version;
		if ( ! function_exists( 'get_plugins' ) ) {
			require_once ABSPATH . 'wp-admin/includes/plugin.php';
		}
		$updates = get_site_transient( 'update_plugins' );
		$active  = (array) get_option( 'active_plugins', array() );
		$plugins = array();
		foreach ( get_plugins() as $file => $p ) {
			$plugins[] = array(
				'file'    => $file,
				'name'    => $p['Name'],
				'version' => $p['Version'],
				'active'  => in_array( $file, $active, true ) || ( is_multisite() && is_plugin_active_for_network( $file ) ),
				'update'  => isset( $updates->response[ $file ]->new_version ) ? $updates->response[ $file ]->new_version : null,
			);
		}
		$types = array();
		foreach ( get_post_types( array( 'show_ui' => true ), 'objects' ) as $pt ) {
			if ( in_array( $pt->name, array( 'wp_block', 'wp_navigation', 'wp_template', 'wp_template_part', 'wp_global_styles', 'elementor_library', 'shop_order', 'shop_coupon', 'shop_order_refund' ), true ) ) {
				continue;
			}
			$c       = wp_count_posts( $pt->name );
			$types[] = array(
				'name'         => $pt->name,
				'label'        => $pt->label,
				'hierarchical' => (bool) $pt->hierarchical,
				'published'    => isset( $c->publish ) ? (int) $c->publish : 0,
				'drafts'       => isset( $c->draft ) ? (int) $c->draft : 0,
				'taxonomies'   => get_object_taxonomies( $pt->name ),
			);
		}
		$theme = wp_get_theme();
		return array(
			'site'        => array(
				'name'       => get_bloginfo( 'name' ),
				'url'        => home_url( '/' ),
				'wordpress'  => $wp_version,
				'php'        => PHP_VERSION,
				'multisite'  => is_multisite(),
				'language'   => get_locale(),
				'timezone'   => wp_timezone_string(),
				'front_page' => 'page' === get_option( 'show_on_front' ) ? (int) get_option( 'page_on_front' ) : 'latest posts',
			),
			'you'         => wp_get_current_user()->user_login,
			'theme'       => array(
				'name'         => $theme->get( 'Name' ),
				'version'      => $theme->get( 'Version' ),
				'parent'       => $theme->parent() ? $theme->parent()->get( 'Name' ) : null,
				'block_theme'  => function_exists( 'wp_is_block_theme' ) && wp_is_block_theme(),
			),
			'builders'    => wpu_bt_builders(),
			'woocommerce' => defined( 'WC_VERSION' ) ? WC_VERSION : null,
			'acf'         => defined( 'ACF_VERSION' ) ? ACF_VERSION . ( defined( 'ACF_PRO' ) && ACF_PRO ? ' (pro)' : '' ) : null,
			'seo_plugin'  => wpu_bt_seo_plugin(),
			'post_types'  => $types,
			'plugins'     => $plugins,
			'abilities'   => function_exists( 'wp_get_abilities' ) ? count( array_filter( wp_get_abilities(), 'wpu_bt_ability_exposed' ) ) : 'needs WordPress 6.9+',
			'bridge'      => array(
				'version'      => WPU_BT_VERSION,
				'read_only'    => (bool) wpu_bt_setting( 'read_only' ),
				'updates'      => (bool) wpu_bt_setting( 'allow_updates' ),
				'tools'        => array_keys( wpu_bt_tools_available() ),
			),
		);
	},
) );

wpu_bt_define_tool( 'site_health_check', array(
	'title'       => 'Health check',
	'description' => 'Loads pages the way a visitor does and reports status codes, load time and error screens (critical error, maintenance, database). Without urls it checks the home page, the newest post and page, and the shop and cart when WooCommerce runs.',
	'props'       => array(
		'urls' => array( 'type' => 'array', 'items' => array( 'type' => 'string' ), 'description' => 'Up to 10 addresses on this site.' ),
	),
	'run'         => function ( $a ) {
		$urls    = ! empty( $a['urls'] ) ? array_map( 'strval', $a['urls'] ) : wpu_bt_default_check_urls();
		$results = wpu_bt_health( $urls );
		$bad     = array_values( array_filter( $results, function ( $r ) {
			return empty( $r['ok'] );
		} ) );
		return array( 'all_ok' => ! $bad, 'pages' => $results );
	},
) );

wpu_bt_define_tool( 'error_log_tail', array(
	'title'       => 'PHP error log',
	'description' => 'The last lines of the PHP error log (debug.log or the server error_log), where fatal errors show up.',
	'props'       => array(
		'lines' => array( 'type' => 'integer', 'description' => '1-500, default 100' ),
	),
	'run'         => function ( $a ) {
		$lines = wpu_bt_int( $a, 'lines', 100, 1, 500 );
		$cands = array();
		if ( defined( 'WP_DEBUG_LOG' ) && is_string( WP_DEBUG_LOG ) ) {
			$cands[] = WP_DEBUG_LOG;
		}
		$cands[] = WP_CONTENT_DIR . '/debug.log';
		$cands[] = ABSPATH . 'error_log';
		$ini     = ini_get( 'error_log' );
		if ( $ini ) {
			$cands[] = $ini;
		}
		foreach ( array_unique( $cands ) as $path ) {
			if ( ! is_readable( $path ) || ! is_file( $path ) ) {
				continue;
			}
			$size = filesize( $path );
			$fh   = fopen( $path, 'rb' ); // phpcs:ignore WordPress.WP.AlternativeFunctions
			if ( ! $fh ) {
				continue;
			}
			// Read only the end of a large log.
			$take = min( $size, 512 * 1024 );
			fseek( $fh, -$take, SEEK_END );
			$chunk = (string) fread( $fh, $take ); // phpcs:ignore WordPress.WP.AlternativeFunctions
			fclose( $fh ); // phpcs:ignore WordPress.WP.AlternativeFunctions
			$all  = preg_split( '/\r?\n/', rtrim( $chunk ) );
			$tail = array_slice( $all, -$lines );
			return array( 'file' => basename( $path ), 'size' => $size, 'lines' => wpu_bt_redact( implode( "\n", $tail ) ) );
		}
		return array( 'file' => null, 'lines' => '', 'note' => 'No readable log. Logging is off: set WP_DEBUG_LOG to true (and WP_DEBUG_DISPLAY to false) in wp-config.php.' );
	},
) );

/** Hide anything that looks like a password or key in log text. */
function wpu_bt_redact( $text ) {
	$text = preg_replace( '/((?:pass(?:word)?|pwd|secret|token|api[_-]?key|auth)["\']?\s*[=:]\s*["\']?)[^"\'\s,;&]+/i', '$1[hidden]', (string) $text );
	return preg_replace( '/\b(wpua|wpur|wpuc|wpu)_[A-Za-z0-9]{20,}\b/', '[hidden]', $text );
}

wpu_bt_define_tool( 'activity_log', array(
	'title'       => 'Bridge tool activity',
	'description' => 'Recent changes and refused calls made through the bridge tools, with which team member made them.',
	'props'       => array( 'limit' => array( 'type' => 'integer', 'description' => '1-200, default 50' ) ),
	'run'         => function ( $a ) {
		$all = array_reverse( (array) get_option( 'wpu_bt_audit', array() ) );
		return array( 'entries' => array_slice( $all, 0, wpu_bt_int( $a, 'limit', 50, 1, 200 ) ) );
	},
) );

wpu_bt_define_tool( 'changes_list', array(
	'title'       => 'Recent changes',
	'description' => 'Changes made through the bridge tools, newest first, each with a change_id that change_undo accepts.',
	'props'       => array( 'limit' => array( 'type' => 'integer', 'description' => '1-200, default 30' ) ),
	'run'         => function ( $a ) {
		$all = array_reverse( (array) get_option( 'wpu_bt_changes', array() ) );
		return array( 'changes' => array_slice( $all, 0, wpu_bt_int( $a, 'limit', 30, 1, 200 ) ) );
	},
) );

wpu_bt_define_tool( 'change_undo', array(
	'title'       => 'Undo a change',
	'description' => 'Put back what a change replaced (content, fields, SEO, Elementor data, ACF values, product data, an order status, or the previous version of an updated plugin or theme). New posts made by content_create go to the trash.',
	'props'       => array( 'change_id' => array( 'type' => 'string' ) ),
	'required'    => array( 'change_id' ),
	'write'       => true,
	'run'         => function ( $a ) {
		return wpu_bt_undo( (string) $a['change_id'] );
	},
) );

/** Undo one change. Used by the change_undo tool. */
function wpu_bt_undo( $id ) {
	$c = wpu_bt_change_find( $id );
	if ( ! $c ) {
		return wpu_bt_err( 'No such change_id.' );
	}
	if ( $c['undone'] ) {
		return wpu_bt_err( 'This change was already undone on ' . $c['undone'] . '.' );
	}
	$p = wpu_bt_change_payload( $id );
	if ( ! $p ) {
		return wpu_bt_err( 'The saved copy for this change is missing or failed its integrity check, so it cannot be undone automatically.' );
	}
	$res = wpu_bt_undo_apply( $p );
	if ( is_wp_error( $res ) ) {
		return $res;
	}
	wpu_bt_change_mark_undone( $id );
	wpu_bt_record( 'undo:' . $c['tool'], array( 'change_id' => $id ) );
	return array( 'undone' => $id, 'summary' => $c['summary'], 'details' => $res );
}

function wpu_bt_undo_apply( array $p ) {
	switch ( isset( $p['kind'] ) ? $p['kind'] : '' ) {
		case 'multi':
			$out = array();
			foreach ( array_reverse( (array) $p['items'] ) as $item ) {
				$r = wpu_bt_undo_apply( (array) $item );
				if ( is_wp_error( $r ) ) {
					return $r;
				}
				$out[] = $r;
			}
			return $out;

		case 'post':
			$id = absint( $p['id'] );
			if ( ! get_post( $id ) || ! current_user_can( 'edit_post', $id ) ) {
				return wpu_bt_err( 'Post ' . $id . ' is gone or you cannot edit it.' );
			}
			$fields       = array_intersect_key( (array) $p['fields'], array_flip( array( 'post_title', 'post_content', 'post_content_filtered', 'post_excerpt', 'post_status', 'post_name', 'post_parent', 'menu_order' ) ) );
			$fields['ID'] = $id;
			kses_remove_filters(); // restoring exactly what was there before
			try {
				$r = wp_update_post( wp_slash( $fields ), true );
			} finally {
				kses_init(); // always back to the normal rule for this user
			}
			if ( is_wp_error( $r ) ) {
				return $r;
			}
			if ( isset( $p['terms'] ) && is_array( $p['terms'] ) ) {
				foreach ( $p['terms'] as $tax => $ids ) {
					wp_set_object_terms( $id, array_map( 'intval', (array) $ids ), sanitize_key( $tax ) );
				}
			}
			if ( array_key_exists( 'thumbnail', $p ) ) {
				$p['thumbnail'] ? set_post_thumbnail( $id, (int) $p['thumbnail'] ) : delete_post_thumbnail( $id );
			}
			clean_post_cache( $id );
			return array( 'post' => $id );

		case 'meta':
			$id = absint( $p['id'] );
			if ( ! get_post( $id ) || ! current_user_can( 'edit_post', $id ) ) {
				return wpu_bt_err( 'Post ' . $id . ' is gone or you cannot edit it.' );
			}
			foreach ( (array) $p['values'] as $key => $value ) {
				if ( null === $value ) {
					delete_post_meta( $id, $key );
				} else {
					update_post_meta( $id, $key, wp_slash( $value ) );
				}
			}
			if ( ! empty( $p['elementor'] ) ) {
				wpu_bt_elementor_flush( $id );
			}
			if ( ! empty( $p['seo'] ) ) {
				wpu_bt_seo_refresh( $id, wpu_bt_seo_plugin() );
			}
			clean_post_cache( $id );
			return array( 'post' => $id, 'fields' => array_keys( (array) $p['values'] ) );

		case 'meta_raw':
			$id  = absint( $p['id'] );
			$key = (string) $p['key'];
			if ( ! get_post( $id ) || ! current_user_can( 'edit_post', $id ) ) {
				return wpu_bt_err( 'Post ' . $id . ' is gone or you cannot edit it.' );
			}
			// Only the builder keys these tools write.
			if ( ! in_array( $key, array( '_elementor_data', '_bricks_page_content_2', '_bricks_page_header_2', '_bricks_page_footer_2', '_fl_builder_data', '_fl_builder_draft', '_breakdance_data' ), true ) ) {
				return wpu_bt_err( 'Unknown field in this change.' );
			}
			wpu_bt_meta_raw_restore( $id, $key, isset( $p['raw'] ) ? $p['raw'] : null );
			wpu_bt_pb_flush( $id, isset( $p['flush'] ) ? (string) $p['flush'] : '' );
			return array( 'post' => $id, 'field' => $key );

		case 'builder_meta':
			return wpu_bt_guard_meta_restore( $p );

		case 'trash':
			$id = absint( $p['id'] );
			if ( get_post( $id ) && current_user_can( 'delete_post', $id ) ) {
				wp_trash_post( $id );
			}
			return array( 'trashed' => $id );

		case 'acf':
			return wpu_bt_acf_undo( $p );
		case 'woo_product':
			return wpu_bt_woo_undo_product( $p );
		case 'woo_order':
			if ( ! wpu_bt_setting( 'allow_orders' ) ) {
				return wpu_bt_err( 'Order changes are switched off on this site (Tools > WPU Bridge).' );
			}
			return wpu_bt_woo_undo_order( $p );
		case 'theme_files':
		case 'theme_switch':
			return wpu_bt_theme_undo( $p );
		case 'files':
			if ( ! wpu_bt_setting( 'allow_updates' ) ) {
				return wpu_bt_err( 'Plugin and theme updates are switched off on this site (Tools > WPU Bridge).' );
			}
			return wpu_bt_updates_undo( $p );
	}
	return wpu_bt_err( 'This kind of change cannot be undone automatically.' );
}
