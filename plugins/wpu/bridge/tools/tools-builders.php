<?php
/**
 * Elementor (read and change text, import templates) and SEO fields (Rank Math, Yoast).
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/* -------------------------------------------------------------------------
 * Elementor
 * ---------------------------------------------------------------------- */

function wpu_bt_has_elementor() {
	return defined( 'ELEMENTOR_VERSION' ) && class_exists( '\Elementor\Plugin' );
}

/** Settings keys that hold visible text. Styling, links, ids and code are never touched. */
function wpu_bt_el_text_key( $key ) {
	$key = (string) $key;
	if ( '' === $key || '_' === $key[0] ) {
		return false;
	}
	if ( preg_match( '/(_size|_color|_typography|_css|_class|_id|url|link|_tag|align|_position|_width|_height|_spacing|_icon|selected_|_animation|_type|_style|_view|_layout|_shape|_skin|_effect|_source|html|shortcode|_code)$/', $key ) ) {
		return false;
	}
	return (bool) preg_match( '/(title|text|editor|description|content|heading|name|job|caption|label|button|prefix|suffix|placeholder|subtitle|before|after|highlighted|rotating|message|testimonial|question|answer|price|period|feature|footer_additional_info|ribbon)/', $key );
}

/** Walk Elementor elements; $fn( &$value, $element, $path ) is called for each text setting. */
function wpu_bt_el_walk( array &$elements, $fn ) {
	foreach ( $elements as &$el ) {
		if ( ! is_array( $el ) ) {
			continue;
		}
		if ( isset( $el['settings'] ) && is_array( $el['settings'] ) ) {
			wpu_bt_el_walk_settings( $el['settings'], $el, '', $fn );
		}
		if ( ! empty( $el['elements'] ) && is_array( $el['elements'] ) ) {
			wpu_bt_el_walk( $el['elements'], $fn );
		}
	}
	unset( $el );
}

function wpu_bt_el_walk_settings( array &$settings, array $el, $prefix, $fn ) {
	foreach ( $settings as $k => &$v ) {
		$path = '' === $prefix ? (string) $k : $prefix . '.' . $k;
		if ( is_array( $v ) ) {
			// Repeaters (tabs, icon lists, slides): lists of items with their own text keys.
			if ( $v && array_keys( $v ) === range( 0, count( $v ) - 1 ) ) {
				foreach ( $v as $i => &$item ) {
					if ( is_array( $item ) ) {
						wpu_bt_el_walk_settings( $item, $el, $path . '.' . $i, $fn );
					}
				}
				unset( $item );
			}
			continue;
		}
		if ( is_string( $v ) && '' !== trim( $v ) && ! is_int( $k ) && wpu_bt_el_text_key( $k ) && preg_match( '/\pL/u', $v ) ) {
			$fn( $v, $el, $path );
		}
	}
	unset( $v );
}

function wpu_bt_el_data( $id ) {
	$raw  = get_post_meta( $id, '_elementor_data', true );
	$data = is_string( $raw ) ? json_decode( $raw, true ) : ( is_array( $raw ) ? $raw : null );
	return array( is_string( $raw ) ? $raw : wp_json_encode( $raw ), is_array( $data ) ? $data : null );
}

/** Replace in text only, never inside HTML tags. */
function wpu_bt_replace_in_text( $value, $find, $replace, &$count ) {
	$parts = wpu_bt_split_markup( $value );
	foreach ( $parts as $i => $part ) {
		if ( 1 === $i % 2 ) {
			continue;
		}
		$n           = 0;
		$parts[ $i ] = str_replace( $find, $replace, $part, $n );
		$count      += $n;
	}
	return implode( '', $parts );
}

/** Make Elementor rebuild the page's CSS and caches after its data changed. */
function wpu_bt_elementor_flush( $id ) {
	delete_post_meta( $id, '_elementor_css' );
	if ( wpu_bt_has_elementor() && isset( \Elementor\Plugin::$instance->files_manager ) ) {
		\Elementor\Plugin::$instance->files_manager->clear_cache();
	}
	clean_post_cache( $id );
	do_action( 'litespeed_purge_post', $id );
	if ( function_exists( 'rocket_clean_post' ) ) {
		rocket_clean_post( $id );
	}
}

wpu_bt_define_tool( 'elementor_page_text', array(
	'title'       => 'Elementor page text',
	'description' => 'Every piece of visible text on an Elementor page or template: headings, text, buttons, list items, tabs, testimonials. Each has the element id and setting path.',
	'cap'         => 'edit_posts',
	'available'   => 'wpu_bt_has_elementor',
	'props'       => array( 'id' => array( 'type' => 'integer' ) ),
	'required'    => array( 'id' ),
	'run'         => function ( $a ) {
		$id = absint( $a['id'] );
		if ( ! get_post( $id ) || ! current_user_can( 'edit_post', $id ) ) {
			return wpu_bt_err( 'No post ' . $id . ' that you can edit.' );
		}
		list( , $data ) = wpu_bt_el_data( $id );
		if ( ! $data ) {
			return wpu_bt_err( 'This post has no Elementor data.' );
		}
		$out = array();
		wpu_bt_el_walk( $data, function ( &$v, $el, $path ) use ( &$out ) {
			if ( count( $out ) < 800 ) {
				$out[] = array(
					'element' => isset( $el['id'] ) ? $el['id'] : '',
					'widget'  => isset( $el['widgetType'] ) ? $el['widgetType'] : ( isset( $el['elType'] ) ? $el['elType'] : '' ),
					'setting' => $path,
					'text'    => wpu_bt_trim( trim( preg_replace( '/\s+/', ' ', wp_strip_all_tags( $v ) ) ), 600 ),
					'html'    => $v !== wp_strip_all_tags( $v ),
				);
			}
		} );
		return array( 'id' => $id, 'title' => get_the_title( $id ), 'texts' => $out );
	},
) );

wpu_bt_define_tool( 'elementor_replace_text', array(
	'title'       => 'Change Elementor text',
	'description' => 'Find and replace visible text on an Elementor page (exact, case-sensitive). Optionally only inside one element. Never changes styling, links or HTML tags. dry_run shows the matches. Saves through Elementor so its CSS is rebuilt, and returns a change_id for undo.',
	'cap'         => 'edit_posts',
	'available'   => 'wpu_bt_has_elementor',
	'props'       => array(
		'id'      => array( 'type' => 'integer' ),
		'find'    => array( 'type' => 'string' ),
		'replace' => array( 'type' => 'string' ),
		'element' => array( 'type' => 'string', 'description' => 'Only this element id (from elementor_page_text).' ),
		'dry_run' => array( 'type' => 'boolean' ),
	),
	'required'    => array( 'id', 'find', 'replace' ),
	'write'       => true,
	'run'         => function ( $a ) {
		$id = absint( $a['id'] );
		if ( ! get_post( $id ) || ! current_user_can( 'edit_post', $id ) ) {
			return wpu_bt_err( 'No post ' . $id . ' that you can edit.' );
		}
		$find    = (string) $a['find'];
		$replace = wp_kses_post( (string) $a['replace'] );
		if ( '' === $find ) {
			return wpu_bt_err( 'find is empty.' );
		}
		list( $raw, $data ) = wpu_bt_el_data( $id );
		if ( ! $data ) {
			return wpu_bt_err( 'This post has no Elementor data.' );
		}
		$only  = wpu_bt_str( $a, 'element' );
		$hits  = array();
		$total = 0;
		wpu_bt_el_walk( $data, function ( &$v, $el, $path ) use ( $find, $replace, $only, &$hits, &$total ) {
			if ( '' !== $only && ( ! isset( $el['id'] ) || $el['id'] !== $only ) ) {
				return;
			}
			$n = 0;
			$new = wpu_bt_replace_in_text( $v, $find, $replace, $n );
			if ( $n ) {
				$hits[] = array( 'element' => isset( $el['id'] ) ? $el['id'] : '', 'setting' => $path, 'count' => $n );
				$total += $n;
				$v      = $new;
			}
		} );
		if ( ! $total ) {
			return array( 'replaced' => 0, 'note' => 'Text not found. Check exact spelling and spaces with elementor_page_text.' );
		}
		if ( wpu_bt_bool( $a, 'dry_run' ) ) {
			return array( 'dry_run' => true, 'would_replace' => $total, 'where' => $hits );
		}
		$saved_with = 'meta';
		$doc        = wpu_bt_has_elementor() && isset( \Elementor\Plugin::$instance->documents ) ? \Elementor\Plugin::$instance->documents->get( $id, false ) : null;
		if ( $doc && method_exists( $doc, 'save' ) ) {
			$doc->save( array( 'elements' => $data ) );
			$saved_with = 'elementor';
		} else {
			update_post_meta( $id, '_elementor_data', wp_slash( wp_json_encode( $data ) ) );
		}
		wpu_bt_elementor_flush( $id );
		$cid = wpu_bt_change_add( 'elementor_replace_text', 'Elementor text on #' . $id . ': "' . substr( $find, 0, 40 ) . '" -> "' . substr( $replace, 0, 40 ) . '" (' . $total . 'x)', array( 'kind' => 'meta', 'id' => $id, 'elementor' => true, 'values' => array( '_elementor_data' => $raw ) ) );
		return array( 'replaced' => $total, 'where' => $hits, 'saved_with' => $saved_with, 'url' => get_permalink( $id ), 'change_id' => $cid );
	},
) );

/** '' when a template has no script-capable content, else the reason. */
function wpu_bt_el_template_risk( $node ) {
	if ( is_array( $node ) ) {
		if ( isset( $node['widgetType'] ) && in_array( $node['widgetType'], array( 'html', 'shortcode', 'code-highlight' ), true ) ) {
			return 'it contains an ' . $node['widgetType'] . ' widget.';
		}
		foreach ( $node as $k => $v ) {
			if ( in_array( (string) $k, array( 'custom_js', 'custom_code', 'custom_html' ), true ) && ! ( is_string( $v ) && '' === trim( $v ) ) ) {
				return 'it contains custom code (' . $k . ').';
			}
			$r = wpu_bt_el_template_risk( $v );
			if ( '' !== $r ) {
				return $r;
			}
		}
		return '';
	}
	if ( is_string( $node ) && preg_match( '/<\s*(script|iframe|object|embed)\b|javascript:|\bon[a-z]+\s*=/i', $node ) ) {
		return 'it contains script, an iframe, a javascript: link or an event handler.';
	}
	return '';
}

wpu_bt_define_tool( 'elementor_template_import', array(
	'title'       => 'Import Elementor template',
	'description' => 'Import an Elementor template export (the JSON from Templates > Saved Templates > Export, or one WP Ultimate Build compiled) into this site\'s template library, through Elementor\'s own importer.',
	'cap'         => 'edit_posts',
	'available'   => 'wpu_bt_has_elementor',
	'props'       => array(
		'template' => array( 'type' => 'object', 'description' => 'The template JSON (with "content", "page_settings", "version", "title", "type").' ),
		'filename' => array( 'type' => 'string' ),
	),
	'required'    => array( 'template' ),
	'write'       => true,
	'run'         => function ( $a ) {
		$json = wp_json_encode( $a['template'] );
		if ( ! $json || strlen( $json ) > 8 * MB_IN_BYTES ) {
			return wpu_bt_err( 'Template is empty or larger than 8 MB.' );
		}
		// Templates go live as stored. Refuse anything that could run script in a visitor's browser.
		$why = wpu_bt_el_template_risk( $a['template'] );
		if ( '' !== $why ) {
			return wpu_bt_err( 'Refused: ' . $why . ' Remove it, or import this template in wp-admin after checking it by hand.' );
		}
		$name = sanitize_file_name( wpu_bt_str( $a, 'filename', 'template.json' ) );
		if ( '.json' !== substr( $name, -5 ) ) {
			$name .= '.json';
		}
		$result = \Elementor\Plugin::$instance->templates_manager->import_template( array(
			'fileName' => $name,
			'fileData' => base64_encode( $json ),
		) );
		if ( is_wp_error( $result ) ) {
			return wpu_bt_err( 'Elementor refused the import: ' . $result->get_error_message() );
		}
		$out   = array();
		$items = array();
		foreach ( (array) $result as $t ) {
			$t     = (array) $t;
			$tid   = (int) ( isset( $t['template_id'] ) ? $t['template_id'] : 0 );
			$out[] = array( 'id' => $tid, 'title' => isset( $t['title'] ) ? (string) $t['title'] : '', 'type' => isset( $t['type'] ) ? (string) $t['type'] : '' );
			if ( $tid ) {
				$items[] = array( 'kind' => 'trash', 'id' => $tid );
			}
		}
		$cid = $items ? wpu_bt_change_add( 'elementor_template_import', 'Imported Elementor template ' . $name, array( 'kind' => 'multi', 'items' => $items ) ) : null;
		return array( 'templates' => $out, 'change_id' => $cid );
	},
) );

/* -------------------------------------------------------------------------
 * SEO fields (same field names as the bridge's /seo route)
 * ---------------------------------------------------------------------- */

function wpu_bt_seo_plugin() {
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

function wpu_bt_seo_map( $plugin ) {
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

function wpu_bt_seo_read( $post_id, $plugin ) {
	$out = array();
	foreach ( wpu_bt_seo_map( $plugin ) as $field => $key ) {
		$val = get_post_meta( $post_id, $key, true );
		if ( 'noindex' === $field ) {
			$out[ $field ] = 'rankmath' === $plugin ? ( is_array( $val ) && in_array( 'noindex', $val, true ) ) : '1' === (string) $val;
			continue;
		}
		$out[ $field ] = '' === (string) $val ? null : (string) $val;
	}
	$schema        = get_post_meta( $post_id, '_wpu_schema', true );
	$out['schema'] = '' === $schema ? null : json_decode( (string) $schema, true );
	return $out;
}

/** Raw meta for undo: every key a write may touch. */
function wpu_bt_seo_raw( $post_id, $plugin ) {
	$keys   = array_values( wpu_bt_seo_map( $plugin ) );
	$keys[] = '_wpu_schema';
	$raw    = array();
	foreach ( $keys as $k ) {
		$raw[ $k ] = metadata_exists( 'post', $post_id, $k ) ? get_post_meta( $post_id, $k, true ) : null;
	}
	return $raw;
}

function wpu_bt_seo_write_field( $id, $plugin, $field, $value ) {
	if ( 'schema' === $field ) {
		if ( null === $value ) {
			delete_post_meta( $id, '_wpu_schema' );
		} else {
			update_post_meta( $id, '_wpu_schema', wp_slash( wp_json_encode( $value ) ) );
		}
		return;
	}
	$map = wpu_bt_seo_map( $plugin );
	$key = $map[ $field ];
	if ( 'noindex' === $field ) {
		if ( 'rankmath' === $plugin ) {
			$robots   = get_post_meta( $id, $key, true );
			$robots   = is_array( $robots ) ? array_values( array_diff( $robots, array( 'noindex', 'index' ) ) ) : array();
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

/** Yoast serves titles from its indexable table: drop the row so it is rebuilt. Then clear known page caches. */
function wpu_bt_seo_refresh( $id, $plugin ) {
	global $wpdb;
	if ( 'yoast' === $plugin ) {
		$table = $wpdb->prefix . 'yoast_indexable';
		// $table comes from $wpdb->prefix, never from input.
		$wpdb->query( $wpdb->prepare( "DELETE FROM {$table} WHERE object_id = %d AND object_type = 'post'", $id ) ); // phpcs:ignore WordPress.DB.PreparedSQL.InterpolatedNotPrepared,WordPress.DB.DirectDatabaseQuery
	}
	clean_post_cache( $id );
	do_action( 'litespeed_purge_post', $id );
	if ( function_exists( 'rocket_clean_post' ) ) {
		rocket_clean_post( $id );
	}
}

/** Print stored JSON-LD when the separate WPU SEO Schema mu-plugin is not installed. */
add_action( 'wp_head', function () {
	if ( function_exists( 'wpu_seo_schema_print' ) || ! is_singular() ) {
		return;
	}
	$raw = get_post_meta( get_queried_object_id(), '_wpu_schema', true );
	$data = is_string( $raw ) && '' !== $raw ? json_decode( $raw, true ) : null;
	if ( ! is_array( $data ) || ! $data ) {
		return;
	}
	if ( array_keys( $data ) === range( 0, count( $data ) - 1 ) ) {
		$data = array( '@context' => 'https://schema.org', '@graph' => array_values( $data ) );
	}
	$json = wp_json_encode( $data, JSON_HEX_TAG | JSON_HEX_AMP | JSON_HEX_APOS | JSON_HEX_QUOT | JSON_UNESCAPED_SLASHES );
	if ( $json ) {
		echo "\n<script type=\"application/ld+json\" class=\"wpu-schema\">" . $json . "</script>\n"; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped -- JSON encoded with HEX flags
	}
}, 30 );

wpu_bt_define_tool( 'seo_get', array(
	'title'       => 'Get SEO fields',
	'description' => 'SEO title, description, focus keyword, canonical, noindex and JSON-LD schema for pages and posts, from Rank Math or Yoast.',
	'cap'         => 'edit_posts',
	'props'       => array(
		'ids'        => array( 'type' => 'array', 'items' => array( 'type' => 'integer' ) ),
		'post_types' => array( 'type' => 'array', 'items' => array( 'type' => 'string' ), 'description' => 'Default page and post.' ),
		'per_page'   => array( 'type' => 'integer', 'description' => '1-200, default 100' ),
		'page'       => array( 'type' => 'integer' ),
	),
	'run'         => function ( $a ) {
		$plugin = wpu_bt_seo_plugin();
		$args   = array(
			'post_type'      => isset( $a['post_types'] ) ? array_map( 'sanitize_key', (array) $a['post_types'] ) : array( 'page', 'post' ),
			'post_status'    => array( 'publish', 'draft', 'pending', 'private', 'future' ),
			'posts_per_page' => wpu_bt_int( $a, 'per_page', 100, 1, 200 ),
			'paged'          => wpu_bt_int( $a, 'page', 1, 1, 10000 ),
			'fields'         => 'ids',
			'orderby'        => 'ID',
			'order'          => 'ASC',
		);
		if ( ! empty( $a['ids'] ) ) {
			$args['post__in']  = array_map( 'absint', (array) $a['ids'] );
			$args['post_type'] = 'any';
		}
		$q    = new WP_Query( $args );
		$rows = array();
		foreach ( $q->posts as $id ) {
			if ( ! current_user_can( 'edit_post', $id ) ) {
				continue;
			}
			$rows[] = array( 'id' => $id, 'type' => get_post_type( $id ), 'title' => get_the_title( $id ), 'url' => get_permalink( $id ), 'seo' => wpu_bt_seo_read( $id, $plugin ) );
		}
		return array( 'seo_plugin' => $plugin, 'writable' => (bool) wpu_bt_seo_map( $plugin ), 'total' => (int) $q->found_posts, 'pages' => $rows );
	},
) );

wpu_bt_define_tool( 'seo_update', array(
	'title'       => 'Update SEO fields',
	'description' => 'Set SEO fields for up to 100 pages: {"items":[{"id":12,"title":"...","description":"...","focus_keyword":"...","canonical":"...","noindex":false,"schema":{...}}]}. Only fields you send change. dry_run (default true) shows the changes first. One change_id undoes the whole batch.',
	'cap'         => 'edit_posts',
	'props'       => array(
		'items'   => array( 'type' => 'array', 'items' => array( 'type' => 'object' ) ),
		'dry_run' => array( 'type' => 'boolean', 'description' => 'Default true.' ),
	),
	'required'    => array( 'items' ),
	'write'       => true,
	'run'         => function ( $a ) {
		$plugin = wpu_bt_seo_plugin();
		if ( ! wpu_bt_seo_map( $plugin ) ) {
			return wpu_bt_err( 'No supported SEO plugin is active (found: ' . $plugin . '). Rank Math or Yoast is needed.' );
		}
		$items = (array) $a['items'];
		if ( count( $items ) > 100 ) {
			return wpu_bt_err( 'At most 100 items per call.' );
		}
		$dry     = wpu_bt_bool( $a, 'dry_run', true );
		$results = array();
		$undo    = array();
		foreach ( $items as $item ) {
			$item = (array) $item;
			$id   = isset( $item['id'] ) ? absint( $item['id'] ) : 0;
			if ( ! $id || ! get_post( $id ) || ! current_user_can( 'edit_post', $id ) ) {
				$results[] = array( 'id' => $id, 'ok' => false, 'error' => 'no such post you can edit' );
				continue;
			}
			$before  = wpu_bt_seo_read( $id, $plugin );
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
			$results[] = array( 'id' => $id, 'ok' => true, 'title' => get_the_title( $id ), 'changes' => $changes ? $changes : new stdClass() );
			if ( $dry || ! $changes ) {
				continue;
			}
			$undo[] = array( 'kind' => 'meta', 'id' => $id, 'seo' => true, 'values' => wpu_bt_seo_raw( $id, $plugin ) );
			foreach ( $changes as $field => $c ) {
				wpu_bt_seo_write_field( $id, $plugin, $field, $c['to'] );
			}
			wpu_bt_seo_refresh( $id, $plugin );
		}
		$out = array( 'dry_run' => $dry, 'seo_plugin' => $plugin, 'results' => $results );
		if ( $undo ) {
			$out['change_id'] = wpu_bt_change_add( 'seo_update', 'SEO fields on ' . count( $undo ) . ' pages', array( 'kind' => 'multi', 'items' => $undo ) );
		}
		return $out;
	},
) );
