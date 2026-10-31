<?php
/**
 * Build a site from a plan file.
 *
 *   powershell -File bin/rplan.ps1 plans/client.plan.json          dry run
 *   powershell -File bin/rplan.ps1 plans/client.plan.json apply    make the changes
 *
 * The plan arrives base64-encoded in $argv (plan_b64=...) - bin/rplan.ps1 does
 * that. Every step compares the site's CURRENT state with the plan first and
 * only changes what differs, so:
 *   - the dry run is an exact list of what apply will do
 *   - re-running after a host killed the request part-way finishes the job
 *     instead of duplicating pages or menu items
 *
 * Output legend:   = already correct    ~ change    + create    ! skipped (reason given)
 *
 * Steps that need a plugin the plan installs (Elementor kit, WooCommerce) show
 * as skipped in a dry run until that plugin exists. Apply in stages: plugins
 * first, then run again.
 */

defined( 'ABSPATH' ) || exit;

$argv  = isset( $argv ) ? (array) $argv : array();
$apply = in_array( 'apply', $argv, true );

$plan_b64 = '';
foreach ( $argv as $a ) {
	if ( 0 === strpos( (string) $a, 'plan_b64=' ) ) {
		$plan_b64 = substr( $a, 9 );
	}
}
$plan = json_decode( (string) base64_decode( $plan_b64 ), true );
if ( ! is_array( $plan ) ) {
	exit( "No plan received. Run this through bin/rplan.ps1 <plan.json>.\n" );
}

// The bridge includes this file inside a function, so plain variables are not
// global - helpers read their state from $GLOBALS explicitly.
$GLOBALS['wpsb_plan'] = array( 'apply' => $apply, 'same' => 0, 'change' => 0, 'skip' => 0, 'flush' => false, 'pages' => array() );

echo $apply ? "== APPLY ==\n" : "== DRY RUN - nothing is changed. Add 'apply' to make these changes. ==\n";

/* ------------------------------------------------------------------ helpers */

function wpsb_plan_h( $title ) {
	echo "\n[" . $title . "]\n";
}

function wpsb_plan_line( $sym, $msg ) {
	$k = '=' === $sym ? 'same' : ( '!' === $sym ? 'skip' : 'change' );
	$GLOBALS['wpsb_plan'][ $k ]++;
	echo '  ' . $sym . ' ' . $msg . "\n";
}

function wpsb_plan_apply() {
	return ! empty( $GLOBALS['wpsb_plan']['apply'] );
}

function wpsb_plan_v( $v ) {
	return ( is_scalar( $v ) || null === $v ) ? var_export( $v, true ) : wp_json_encode( $v );
}

/** Set an option only if it differs; scalars compared as strings ('0' vs 0). */
function wpsb_plan_option( $name, $value, $label = '' ) {
	$label = $label ? $label : $name;
	$cur   = get_option( $name, null );
	$same  = ( is_scalar( $cur ) && is_scalar( $value ) ) ? ( (string) $cur === (string) $value ) : ( $cur == $value ); // phpcs:ignore
	if ( $same ) {
		wpsb_plan_line( '=', "$label is " . wpsb_plan_v( $value ) );
		return false;
	}
	wpsb_plan_line( '~', "$label: " . wpsb_plan_v( $cur ) . ' -> ' . wpsb_plan_v( $value ) );
	if ( wpsb_plan_apply() ) {
		update_option( $name, $value );
	}
	return true;
}

/** Find a published Elementor library template by exact title, or by ID. */
function wpsb_plan_template( $ref ) {
	if ( is_numeric( $ref ) ) {
		$p = get_post( (int) $ref );
		return ( $p && 'elementor_library' === $p->post_type ) ? $p : null;
	}
	$found = get_posts( array( 'post_type' => 'elementor_library', 'post_status' => 'publish', 'title' => (string) $ref, 'numberposts' => 2 ) );
	if ( count( $found ) > 1 ) {
		wpsb_plan_line( '!', "more than one template titled \"$ref\" - use its ID in the plan" );
		return null;
	}
	return $found ? $found[0] : null;
}

function wpsb_plan_admin_includes() {
	require_once ABSPATH . 'wp-admin/includes/plugin.php';
	require_once ABSPATH . 'wp-admin/includes/file.php';
	require_once ABSPATH . 'wp-admin/includes/misc.php';
	require_once ABSPATH . 'wp-admin/includes/class-wp-upgrader.php';
	require_once ABSPATH . 'wp-admin/includes/plugin-install.php';
	require_once ABSPATH . 'wp-admin/includes/theme.php';
	require_once ABSPATH . 'wp-admin/includes/nav-menu.php';
}
wpsb_plan_admin_includes();

/* --------------------------------------------------------------------- site */

if ( ! empty( $plan['site'] ) ) {
	$s = $plan['site'];
	wpsb_plan_h( 'site' );
	if ( isset( $s['title'] ) ) { wpsb_plan_option( 'blogname', $s['title'], 'site title' ); }
	if ( isset( $s['tagline'] ) ) { wpsb_plan_option( 'blogdescription', $s['tagline'], 'tagline' ); }
	if ( isset( $s['timezone'] ) ) { wpsb_plan_option( 'timezone_string', $s['timezone'], 'timezone' ); }
	if ( isset( $s['date_format'] ) ) { wpsb_plan_option( 'date_format', $s['date_format'], 'date format' ); }
	if ( isset( $s['discourage_search_engines'] ) ) {
		wpsb_plan_option( 'blog_public', $s['discourage_search_engines'] ? '0' : '1', 'search engines ' . ( $s['discourage_search_engines'] ? 'discouraged (build mode)' : 'allowed' ) );
	}
	if ( isset( $s['permalinks'] ) && wpsb_plan_option( 'permalink_structure', $s['permalinks'], 'permalinks' ) ) {
		$GLOBALS['wpsb_plan']['flush'] = true;
	}

	if ( ! empty( $s['remove_default_content'] ) ) {
		// Only the untouched WordPress defaults: never modified since install.
		foreach ( array( array( 'hello-world', 'post' ), array( 'sample-page', 'page' ) ) as $d ) {
			$p = get_page_by_path( $d[0], OBJECT, $d[1] );
			if ( ! $p || 'trash' === $p->post_status ) {
				wpsb_plan_line( '=', "default {$d[1]} \"{$d[0]}\" not present" );
			} elseif ( $p->post_modified_gmt !== $p->post_date_gmt ) {
				wpsb_plan_line( '!', "\"{$p->post_title}\" has been edited since install - left alone" );
			} else {
				wpsb_plan_line( '~', "trash default {$d[1]} \"{$p->post_title}\" (#{$p->ID})" );
				if ( wpsb_plan_apply() ) { wp_trash_post( $p->ID ); }
			}
		}
		$c = get_comment( 1 );
		if ( $c && 'A WordPress Commenter' === $c->comment_author && 'trash' !== $c->comment_approved ) {
			wpsb_plan_line( '~', 'trash the default "A WordPress Commenter" comment' );
			if ( wpsb_plan_apply() ) { wp_trash_comment( 1 ); }
		}
	}
}

/* ------------------------------------------------------------------ plugins */

if ( ! empty( $plan['plugins'] ) ) {
	wpsb_plan_h( 'plugins' );
	$installed = get_plugins();

	foreach ( (array) ( $plan['plugins']['install'] ?? array() ) as $slug ) {
		$slug = sanitize_key( $slug );
		$file = '';
		foreach ( array_keys( $installed ) as $f ) {
			if ( 0 === strpos( $f, $slug . '/' ) ) { $file = $f; break; }
		}
		if ( ! $file ) {
			wpsb_plan_line( '+', "install $slug from wordpress.org and activate" );
			if ( ! wpsb_plan_apply() ) { continue; }
			$api = plugins_api( 'plugin_information', array( 'slug' => $slug, 'fields' => array( 'sections' => false ) ) );
			if ( is_wp_error( $api ) ) { wpsb_plan_line( '!', "$slug: " . $api->get_error_message() ); continue; }
			$up  = new Plugin_Upgrader( new Automatic_Upgrader_Skin() );
			$res = $up->install( $api->download_link );
			if ( true !== $res ) {
				$err = is_wp_error( $res ) ? $res->get_error_message() : implode( ' ', (array) $up->skin->get_upgrade_messages() );
				wpsb_plan_line( '!', "$slug install failed: " . ( $err ?: 'unknown error (filesystem not writable by PHP?)' ) );
				continue;
			}
			$file = $up->plugin_info();
		}
		if ( is_plugin_active( $file ) ) {
			wpsb_plan_line( '=', "$slug active" );
		} else {
			wpsb_plan_line( '~', "activate $file" );
			if ( wpsb_plan_apply() ) {
				$r = activate_plugin( $file );
				if ( is_wp_error( $r ) ) { wpsb_plan_line( '!', "$file: " . $r->get_error_message() ); }
			}
		}
	}

	foreach ( (array) ( $plan['plugins']['activate'] ?? array() ) as $file ) {
		if ( ! isset( $installed[ $file ] ) ) {
			wpsb_plan_line( '!', "$file is not installed - use \"install\" with its wordpress.org slug, or upload it" );
		} elseif ( is_plugin_active( $file ) ) {
			wpsb_plan_line( '=', "$file active" );
		} else {
			wpsb_plan_line( '~', "activate $file" );
			if ( wpsb_plan_apply() ) {
				$r = activate_plugin( $file );
				if ( is_wp_error( $r ) ) { wpsb_plan_line( '!', "$file: " . $r->get_error_message() ); }
			}
		}
	}
	// First-run wizards would hijack the next wp-admin visit.
	if ( wpsb_plan_apply() ) {
		delete_transient( '_wc_activation_redirect' );
		delete_transient( 'elementor_activation_redirect' );
	}
}

/* -------------------------------------------------------------------- theme */

if ( ! empty( $plan['theme'] ) ) {
	wpsb_plan_h( 'theme' );
	$t = $plan['theme'];
	if ( ! empty( $t['install'] ) ) {
		$slug = sanitize_key( $t['install'] );
		if ( wp_get_theme( $slug )->exists() ) {
			wpsb_plan_line( '=', "theme $slug installed" );
		} else {
			wpsb_plan_line( '+', "install theme $slug from wordpress.org" );
			if ( wpsb_plan_apply() ) {
				$api = themes_api( 'theme_information', array( 'slug' => $slug, 'fields' => array( 'sections' => false ) ) );
				if ( is_wp_error( $api ) ) {
					wpsb_plan_line( '!', "$slug: " . $api->get_error_message() );
				} else {
					$up  = new Theme_Upgrader( new Automatic_Upgrader_Skin() );
					$res = $up->install( $api->download_link );
					if ( true !== $res ) { wpsb_plan_line( '!', "theme $slug install failed" ); }
				}
			}
		}
	}
	if ( ! empty( $t['activate'] ) ) {
		$want = $t['activate'];
		if ( get_stylesheet() === $want ) {
			wpsb_plan_line( '=', "active theme is $want" );
		} elseif ( ! wp_get_theme( $want )->exists() && wpsb_plan_apply() ) {
			wpsb_plan_line( '!', "theme $want is not installed" );
		} else {
			wpsb_plan_line( '~', 'switch theme ' . get_stylesheet() . " -> $want" );
			if ( wpsb_plan_apply() && wp_get_theme( $want )->exists() ) { switch_theme( $want ); }
		}
	}
}

/* ---------------------------------------------------------- elementor + kit */

$has_elementor = class_exists( '\Elementor\Plugin' );

if ( ! empty( $plan['elementor'] ) ) {
	wpsb_plan_h( 'elementor settings' );
	if ( ! $has_elementor ) {
		wpsb_plan_line( '!', 'Elementor is not active yet - apply the plugins step, then run again' );
	} else {
		$e = $plan['elementor'];
		if ( isset( $e['disable_default_colors'] ) ) { wpsb_plan_option( 'elementor_disable_color_schemes', $e['disable_default_colors'] ? 'yes' : '', 'disable Elementor default colours' ); }
		if ( isset( $e['disable_default_fonts'] ) ) { wpsb_plan_option( 'elementor_disable_typography_schemes', $e['disable_default_fonts'] ? 'yes' : '', 'disable Elementor default fonts' ); }
		if ( isset( $e['container'] ) ) { wpsb_plan_option( 'elementor_experiment-container', $e['container'] ? 'active' : 'inactive', 'Flexbox Container' ); }
		if ( isset( $e['load_google_fonts_locally'] ) ) { wpsb_plan_option( 'elementor_local_google_fonts', $e['load_google_fonts_locally'] ? '1' : '0', 'load Google Fonts locally' ); }
	}
}

if ( ! empty( $plan['kit'] ) ) {
	wpsb_plan_h( 'elementor kit (global colours + fonts)' );
	$kit = (int) get_option( 'elementor_active_kit' );
	$s   = $kit ? get_post_meta( $kit, '_elementor_page_settings', true ) : null;
	if ( ! $has_elementor || ! $kit ) {
		wpsb_plan_line( '!', 'no active Elementor kit yet - apply the plugins step, then run again' );
	} else {
		$s    = is_array( $s ) ? $s : array();
		$orig = $s;

		foreach ( (array) ( $plan['kit']['colors'] ?? array() ) as $id => $hex ) {
			$found = false;
			foreach ( (array) ( $s['system_colors'] ?? array() ) as $i => $c ) {
				if ( ( $c['_id'] ?? '' ) === $id ) {
					$found = true;
					if ( strtoupper( $c['color'] ?? '' ) === strtoupper( $hex ) ) {
						wpsb_plan_line( '=', "colour $id $hex" );
					} else {
						wpsb_plan_line( '~', "colour $id " . ( $c['color'] ?? '(none)' ) . " -> $hex" );
						$s['system_colors'][ $i ]['color'] = $hex;
					}
				}
			}
			if ( ! $found ) {
				wpsb_plan_line( '+', "colour $id $hex" );
				$s['system_colors'][] = array( '_id' => $id, 'title' => ucfirst( $id ), 'color' => $hex );
			}
		}

		foreach ( (array) ( $plan['kit']['fonts'] ?? array() ) as $id => $f ) {
			$fam   = $f['family'] ?? '';
			$w     = (string) ( $f['weight'] ?? '400' );
			$found = false;
			foreach ( (array) ( $s['system_typography'] ?? array() ) as $i => $t ) {
				if ( ( $t['_id'] ?? '' ) === $id ) {
					$found = true;
					if ( ( $t['typography_font_family'] ?? '' ) === $fam && (string) ( $t['typography_font_weight'] ?? '' ) === $w ) {
						wpsb_plan_line( '=', "font $id $fam $w" );
					} else {
						wpsb_plan_line( '~', "font $id " . ( $t['typography_font_family'] ?? '(none)' ) . " -> $fam $w" );
						$s['system_typography'][ $i ] = array_merge( $t, array( 'typography_typography' => 'custom', 'typography_font_family' => $fam, 'typography_font_weight' => $w ) );
					}
				}
			}
			if ( ! $found ) {
				wpsb_plan_line( '+', "font $id $fam $w" );
				$s['system_typography'][] = array( '_id' => $id, 'title' => ucfirst( $id ), 'typography_typography' => 'custom', 'typography_font_family' => $fam, 'typography_font_weight' => $w );
			}
		}

		// Families that theme/widget CSS names but nothing loads (audit/fonts.mjs):
		// a custom global typography entry makes Elementor enqueue them site-wide.
		$have = array_map( function ( $t ) { return $t['typography_font_family'] ?? ''; }, (array) ( $s['custom_typography'] ?? array() ) );
		foreach ( (array) ( $plan['kit']['extra_fonts'] ?? array() ) as $fam ) {
			if ( in_array( $fam, $have, true ) ) {
				wpsb_plan_line( '=', "site-wide font $fam" );
			} else {
				wpsb_plan_line( '+', "site-wide font $fam" );
				$s['custom_typography'][] = array( '_id' => 'wpsb' . substr( md5( $fam ), 0, 5 ), 'title' => "$fam (site-wide)", 'typography_typography' => 'custom', 'typography_font_family' => $fam, 'typography_font_weight' => '600' );
			}
		}

		if ( $s !== $orig && wpsb_plan_apply() ) {
			if ( false === get_option( '_wpsb_kit_settings_orig', false ) ) {
				add_option( '_wpsb_kit_settings_orig', $orig, '', false ); // first-ever state, for rollback
			}
			update_post_meta( $kit, '_elementor_page_settings', wp_slash( $s ) );
			delete_post_meta( $kit, '_elementor_css' );
			if ( class_exists( '\Elementor\Core\Files\CSS\Post' ) ) {
				\Elementor\Core\Files\CSS\Post::create( $kit )->update();
			}
			echo "    kit saved and its CSS regenerated (first-ever settings kept in _wpsb_kit_settings_orig)\n";
		}
	}
}

/* -------------------------------------------------------------------- pages */

if ( ! empty( $plan['pages'] ) ) {
	wpsb_plan_h( 'pages' );
	foreach ( (array) $plan['pages'] as $pg ) {
		$slug   = sanitize_title( $pg['slug'] ?? '' );
		$title  = (string) ( $pg['title'] ?? $slug );
		$status = (string) ( $pg['status'] ?? 'publish' );
		if ( '' === $slug ) { wpsb_plan_line( '!', 'a page has no slug - skipped' ); continue; }

		$parent_id = 0;
		if ( ! empty( $pg['parent'] ) ) {
			$parent_id = $GLOBALS['wpsb_plan']['pages'][ $pg['parent'] ] ?? ( get_page_by_path( $pg['parent'] ) ? get_page_by_path( $pg['parent'] )->ID : 0 );
		}
		$path = $parent_id ? get_page_uri( $parent_id ) . '/' . $slug : $slug;
		$p    = get_page_by_path( $path, OBJECT, 'page' );

		if ( ! $p ) {
			wpsb_plan_line( '+', "page \"$title\" /$path/ ($status)" );
			if ( ! wpsb_plan_apply() ) { continue; }
			$id = wp_insert_post( array( 'post_type' => 'page', 'post_title' => $title, 'post_name' => $slug, 'post_status' => $status, 'post_parent' => $parent_id ), true );
			if ( is_wp_error( $id ) ) { wpsb_plan_line( '!', "$slug: " . $id->get_error_message() ); continue; }
			$p = get_post( $id );
			$GLOBALS['wpsb_plan']['flush'] = true;
		} else {
			$upd = array();
			if ( $p->post_title !== $title ) { $upd['post_title'] = $title; }
			if ( $p->post_status !== $status ) { $upd['post_status'] = $status; }
			if ( $upd ) {
				wpsb_plan_line( '~', "page /$path/ " . wp_json_encode( $upd ) );
				if ( wpsb_plan_apply() ) { wp_update_post( array( 'ID' => $p->ID ) + $upd ); }
			} else {
				wpsb_plan_line( '=', "page \"$title\" /$path/ #{$p->ID}" );
			}
		}
		$GLOBALS['wpsb_plan']['pages'][ $slug ] = $p->ID;

		if ( ! empty( $pg['page_template'] ) ) {
			$cur = get_post_meta( $p->ID, '_wp_page_template', true );
			if ( $cur === $pg['page_template'] ) {
				wpsb_plan_line( '=', "  /$path/ page template {$pg['page_template']}" );
			} else {
				wpsb_plan_line( '~', "  /$path/ page template " . ( $cur ?: 'default' ) . " -> {$pg['page_template']}" );
				if ( wpsb_plan_apply() ) { update_post_meta( $p->ID, '_wp_page_template', $pg['page_template'] ); }
			}
		}

		// Plain post content (e.g. a shortcode) for a page that is not built in Elementor. Only fills an empty
		// page - existing content is kept unless the entry says "overwrite": true.
		if ( isset( $pg['content'] ) && ! empty( $p->ID ) ) {
			$cur = trim( (string) get_post_field( 'post_content', $p->ID ) );
			if ( $cur === trim( (string) $pg['content'] ) ) {
				wpsb_plan_line( '=', "  /$path/ content" );
			} elseif ( '' !== $cur && empty( $pg['overwrite'] ) ) {
				wpsb_plan_line( '=', "  /$path/ already has content (add \"overwrite\": true to replace it)" );
			} else {
				wpsb_plan_line( '~', "  /$path/ content -> " . mb_substr( (string) $pg['content'], 0, 70 ) );
				if ( wpsb_plan_apply() ) { wp_update_post( array( 'ID' => $p->ID, 'post_content' => wp_slash( (string) $pg['content'] ) ) ); }
			}
		}

		if ( ! empty( $pg['elementor_template'] ) ) {
			if ( ! $has_elementor ) { wpsb_plan_line( '!', "  /$path/ needs Elementor for its template" ); continue; }
			$tpl = wpsb_plan_template( $pg['elementor_template'] );
			if ( ! $tpl ) { wpsb_plan_line( '!', "  /$path/ template \"{$pg['elementor_template']}\" not found - import it first with bin/rtemplate.ps1" ); continue; }
			$has = get_post_meta( $p->ID, '_elementor_data', true );
			if ( $has && '[]' !== $has && empty( $pg['overwrite'] ) ) {
				wpsb_plan_line( '=', "  /$path/ already has Elementor content (add \"overwrite\": true to replace it with \"{$tpl->post_title}\")" );
				continue;
			}
			$raw      = get_post_meta( $tpl->ID, '_elementor_data', true );
			$elements = is_string( $raw ) ? json_decode( $raw, true ) : $raw;
			if ( ! is_array( $elements ) ) { wpsb_plan_line( '!', "  template #{$tpl->ID} has unreadable _elementor_data - not copied" ); continue; }
			wpsb_plan_line( '~', "  /$path/ content from template \"{$tpl->post_title}\" (#{$tpl->ID}, " . count( $elements ) . ' top-level elements)' );
			if ( wpsb_plan_apply() ) {
				$settings = get_post_meta( $tpl->ID, '_elementor_page_settings', true );
				$doc      = \Elementor\Plugin::$instance->documents->get( $p->ID, false );
				update_post_meta( $p->ID, '_elementor_edit_mode', 'builder' );
				if ( $doc ) {
					$doc->save( array( 'elements' => $elements, 'settings' => is_array( $settings ) ? $settings : array() ) );
				} else {
					update_post_meta( $p->ID, '_elementor_data', wp_slash( wp_json_encode( $elements ) ) );
					update_post_meta( $p->ID, '_elementor_template_type', 'wp-page' );
					update_post_meta( $p->ID, '_elementor_version', ELEMENTOR_VERSION );
				}
				delete_post_meta( $p->ID, '_elementor_css' );
			}
		}
	}
}

/* ------------------------------------------------- front page + posts page */

if ( ! empty( $plan['front_page'] ) || ! empty( $plan['posts_page'] ) ) {
	wpsb_plan_h( 'reading settings' );
	$find = function ( $slug ) {
		if ( isset( $GLOBALS['wpsb_plan']['pages'][ $slug ] ) ) { return (int) $GLOBALS['wpsb_plan']['pages'][ $slug ]; }
		$p = get_page_by_path( $slug );
		return $p ? (int) $p->ID : 0;
	};
	if ( ! empty( $plan['front_page'] ) ) {
		$id = $find( $plan['front_page'] );
		if ( ! $id ) {
			wpsb_plan_line( '!', "front page \"{$plan['front_page']}\" does not exist yet" . ( wpsb_plan_apply() ? '' : ' (created on apply)' ) );
		} else {
			wpsb_plan_option( 'show_on_front', 'page', 'homepage shows a static page' );
			wpsb_plan_option( 'page_on_front', $id, "front page = /{$plan['front_page']}/" );
		}
	}
	if ( ! empty( $plan['posts_page'] ) ) {
		$id = $find( $plan['posts_page'] );
		if ( $id ) { wpsb_plan_option( 'page_for_posts', $id, "posts page = /{$plan['posts_page']}/" ); }
		else { wpsb_plan_line( '!', "posts page \"{$plan['posts_page']}\" does not exist yet" ); }
	}
}

/* -------------------------------------------------------------------- menus */

if ( ! empty( $plan['menus'] ) ) {
	wpsb_plan_h( 'menus' );
	$registered = get_registered_nav_menus();
	foreach ( (array) $plan['menus'] as $m ) {
		$name = (string) ( $m['name'] ?? '' );
		if ( '' === $name ) { continue; }

		// Desired items as comparable rows.
		$want = array();
		foreach ( (array) ( $m['items'] ?? array() ) as $it ) {
			if ( ! empty( $it['page'] ) ) {
				$pid = $GLOBALS['wpsb_plan']['pages'][ $it['page'] ] ?? ( get_page_by_path( $it['page'] ) ? get_page_by_path( $it['page'] )->ID : 0 );
				if ( ! $pid ) { wpsb_plan_line( '!', "$name: page \"{$it['page']}\" not found - item skipped" ); continue; }
				$want[] = array( 'type' => 'post_type', 'object' => 'page', 'id' => (int) $pid, 'title' => (string) ( $it['title'] ?? '' ), 'url' => '' );
			} elseif ( ! empty( $it['url'] ) ) {
				$u      = preg_match( '#^https?://#', $it['url'] ) ? $it['url'] : home_url( $it['url'] );
				$want[] = array( 'type' => 'custom', 'object' => 'custom', 'id' => 0, 'title' => (string) ( $it['title'] ?? $u ), 'url' => $u );
			}
		}

		$menu = wp_get_nav_menu_object( $name );
		$have = array();
		if ( $menu ) {
			foreach ( (array) wp_get_nav_menu_items( $menu->term_id ) as $i ) {
				$have[] = array( 'type' => $i->type, 'object' => $i->object, 'id' => (int) $i->object_id, 'title' => 'custom' === $i->type ? $i->title : ( $i->post_title ?: '' ), 'url' => 'custom' === $i->type ? $i->url : '' );
			}
		}
		$sig = function ( $rows ) { return wp_json_encode( array_map( function ( $r ) { return array( $r['type'], $r['id'], $r['url'], $r['title'] ); }, $rows ) ); };

		if ( ! $menu ) {
			wpsb_plan_line( '+', "menu \"$name\" with " . count( $want ) . ' items' );
		} elseif ( $sig( $have ) === $sig( $want ) ) {
			wpsb_plan_line( '=', "menu \"$name\" (" . count( $want ) . ' items)' );
		} else {
			wpsb_plan_line( '~', "menu \"$name\": rebuild items (" . count( $have ) . ' -> ' . count( $want ) . ') - custom classes on old items are not kept' );
		}

		if ( wpsb_plan_apply() && ( ! $menu || $sig( $have ) !== $sig( $want ) ) ) {
			$menu_id = $menu ? $menu->term_id : wp_create_nav_menu( $name );
			if ( is_wp_error( $menu_id ) ) { wpsb_plan_line( '!', "$name: " . $menu_id->get_error_message() ); continue; }
			foreach ( (array) wp_get_nav_menu_items( $menu_id ) as $old ) { wp_delete_post( $old->ID, true ); }
			$pos = 1;
			foreach ( $want as $w ) {
				$args = array( 'menu-item-status' => 'publish', 'menu-item-position' => $pos++ );
				if ( 'custom' === $w['type'] ) {
					$args += array( 'menu-item-type' => 'custom', 'menu-item-title' => $w['title'], 'menu-item-url' => $w['url'] );
				} else {
					$args += array( 'menu-item-type' => 'post_type', 'menu-item-object' => 'page', 'menu-item-object-id' => $w['id'] );
					if ( '' !== $w['title'] ) { $args['menu-item-title'] = $w['title']; }
				}
				wp_update_nav_menu_item( $menu_id, 0, $args );
			}
			$menu = wp_get_nav_menu_object( $menu_id );
		}

		if ( ! empty( $m['location'] ) ) {
			$loc = $m['location'];
			if ( ! isset( $registered[ $loc ] ) ) {
				wpsb_plan_line( '!', "location \"$loc\" is not registered by this theme (it has: " . ( $registered ? implode( ', ', array_keys( $registered ) ) : 'none - Elementor headers use a Nav Menu widget instead' ) . ')' );
			} else {
				$locs = (array) get_theme_mod( 'nav_menu_locations', array() );
				$mid  = $menu ? (int) $menu->term_id : 0;
				if ( $mid && (int) ( $locs[ $loc ] ?? 0 ) === $mid ) {
					wpsb_plan_line( '=', "\"$name\" assigned to $loc" );
				} else {
					wpsb_plan_line( '~', "assign \"$name\" to $loc" );
					if ( wpsb_plan_apply() && $mid ) { $locs[ $loc ] = $mid; set_theme_mod( 'nav_menu_locations', $locs ); }
				}
			}
		}
	}
}

/* ------------------------------------------ Elementor Pro theme builder */

if ( ! empty( $plan['theme_builder'] ) ) {
	wpsb_plan_h( 'theme builder (header / footer / archive conditions)' );
	$tb = class_exists( '\ElementorPro\Modules\ThemeBuilder\Module' ) ? \ElementorPro\Modules\ThemeBuilder\Module::instance() : null;
	if ( ! $tb ) {
		wpsb_plan_line( '!', 'Elementor Pro is not active - display conditions need it' );
	} else {
		foreach ( (array) $plan['theme_builder'] as $row ) {
			$tpl = wpsb_plan_template( $row['template'] ?? '' );
			if ( ! $tpl ) { wpsb_plan_line( '!', 'template "' . ( $row['template'] ?? '' ) . '" not found - import it with bin/rtemplate.ps1' ); continue; }
			$want = array_values( (array) ( $row['conditions'] ?? array() ) );
			$have = array_values( (array) get_post_meta( $tpl->ID, '_elementor_conditions', true ) );
			$type = get_post_meta( $tpl->ID, '_elementor_template_type', true );
			if ( $have === $want ) {
				wpsb_plan_line( '=', "\"{$tpl->post_title}\" ($type) " . implode( ', ', $want ) );
				continue;
			}
			wpsb_plan_line( '~', "\"{$tpl->post_title}\" ($type) conditions " . ( $have ? implode( ', ', $have ) : '(none)' ) . ' -> ' . implode( ', ', $want ) );
			if ( wpsb_plan_apply() ) {
				try {
					$tb->get_conditions_manager()->save_conditions( $tpl->ID, $want );
				} catch ( \Throwable $e ) {
					update_post_meta( $tpl->ID, '_elementor_conditions', $want );
					$tb->get_conditions_manager()->get_cache()->regenerate();
				}
			}
		}
	}
}

/* -------------------------------------------------------------- woocommerce */

if ( ! empty( $plan['woocommerce'] ) ) {
	wpsb_plan_h( 'woocommerce' );
	if ( ! class_exists( 'WooCommerce' ) ) {
		wpsb_plan_line( '!', 'WooCommerce is not active yet - apply the plugins step, then run again' );
	} else {
		$w = $plan['woocommerce'];
		if ( ! empty( $w['create_pages'] ) ) {
			$missing = array_filter( array( 'shop', 'cart', 'checkout', 'myaccount' ), function ( $k ) { return wc_get_page_id( $k ) <= 0 || 'publish' !== get_post_status( wc_get_page_id( $k ) ); } );
			if ( ! $missing ) {
				wpsb_plan_line( '=', 'shop, cart, checkout and my-account pages exist' );
			} else {
				wpsb_plan_line( '+', 'create missing WooCommerce pages: ' . implode( ', ', $missing ) );
				if ( wpsb_plan_apply() ) { WC_Install::create_pages(); $GLOBALS['wpsb_plan']['flush'] = true; }
			}
		}
		if ( isset( $w['currency'] ) ) { wpsb_plan_option( 'woocommerce_currency', $w['currency'], 'currency' ); }
		if ( isset( $w['base_country'] ) ) { wpsb_plan_option( 'woocommerce_default_country', $w['base_country'], 'store country' ); }
		if ( isset( $w['prices_include_tax'] ) ) { wpsb_plan_option( 'woocommerce_prices_include_tax', $w['prices_include_tax'] ? 'yes' : 'no', 'prices entered with tax' ); }
	}
}

/* ------------------------------------------------------------ other options */

if ( ! empty( $plan['options'] ) ) {
	wpsb_plan_h( 'options' );
	foreach ( (array) $plan['options'] as $k => $v ) {
		if ( 0 === strpos( $k, '_' ) ) { continue; } // _comment etc.
		wpsb_plan_option( $k, $v );
	}
}

/* ------------------------------------------------------------------- finish */

if ( wpsb_plan_apply() && ! empty( $GLOBALS['wpsb_plan']['flush'] ) ) {
	flush_rewrite_rules( false );
	echo "\n  rewrite rules flushed\n";
}

$st = $GLOBALS['wpsb_plan'];
printf(
	"\n%d already correct, %d %s, %d skipped.\n",
	$st['same'],
	$st['change'],
	$apply ? 'changed' : 'to change',
	$st['skip']
);
if ( ! $apply && $st['change'] ) {
	echo "Nothing was changed. Review the list above, then re-run with 'apply'.\n";
}
if ( $apply ) {
	echo "Next: node audit/audit.mjs, node audit/fonts.mjs and node audit/sweep.mjs - then look at the screenshots.\n";
}
