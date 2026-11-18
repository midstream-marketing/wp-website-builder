<?php
/**
 * Page builders beyond Elementor: Divi (4 shortcodes and 5 blocks), Bricks, Beaver Builder, Breakdance,
 * SeedProd - plus Gutenberg/classic pages and Elementor through the same two tools.
 *
 * Each builder keeps a page in its own format. For each one these tools read every piece of visible text
 * and replace text inside it, never touching styling, links, ids or HTML tags. The exact stored value is
 * kept for undo (byte for byte, including serialized objects), and the builder's cache is cleared.
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/* -------------------------------------------------------------------------
 * Which keys hold visible text, for any builder's data
 * ---------------------------------------------------------------------- */

function wpu_bt_textish_key( $key ) {
	$key = strtolower( (string) $key );
	if ( '' === $key || '_' === $key[0] || is_numeric( $key ) ) {
		return false;
	}
	if ( preg_match( '/(admin|url|link|href|src|_id$|^id$|class|css|style|color|colour|font|size|width|height|_tag$|^tag$|tags$|icon|align|animation|position|spacing|margin|padding|border|shadow|background|gradient|opacity|_type$|^type$|layout|skin|effect|source|html|shortcode|code|script|target|rel$|nofollow|query|filter|order|breakpoint|responsive|visibility|attr|data_|selector)/', $key ) ) {
		return false;
	}
	return (bool) preg_match( '/(title|text|txt|editor|description|desc|content|heading|headline|subhead|caption|label|button|btn|prefix|suffix|placeholder|subtitle|before|after|highlighted|rotating|message|testimonial|quote|question|answer|name|job|position_text|price|period|feature|footer|ribbon|alt)/', $key );
}

/**
 * Walk arrays and objects; call $fn( &$string, $path ) for each visible-text string.
 * A string counts when its own key is text-ish, or (Divi 5) it is the "value" of an "innerContent" whose
 * parent key is text-ish, or the "text" inside such a value.
 */
function wpu_bt_walk_text( &$node, $fn, array $path = array() ) {
	if ( is_array( $node ) ) {
		foreach ( $node as $k => &$v ) {
			wpu_bt_walk_text_item( $v, $k, $fn, $path );
		}
		unset( $v );
	} elseif ( is_object( $node ) ) {
		foreach ( array_keys( get_object_vars( $node ) ) as $k ) {
			$v = $node->$k;
			wpu_bt_walk_text_item( $v, $k, $fn, $path );
			$node->$k = $v;
		}
	}
}

function wpu_bt_walk_text_item( &$v, $k, $fn, array $path ) {
	$here = array_merge( $path, array( (string) $k ) );
	if ( is_array( $v ) || is_object( $v ) ) {
		wpu_bt_walk_text( $v, $fn, $here );
		return;
	}
	if ( ! is_string( $v ) || '' === trim( $v ) || ! preg_match( '/\pL/u', $v ) || is_int( $k ) ) {
		return;
	}
	$is_text = wpu_bt_textish_key( $k );
	if ( ! $is_text ) {
		// Divi 5: {"title":{"innerContent":{"desktop":{"value":"Hello"}}}} or button value {"text":...}
		$i = array_search( 'innerContent', $path, true );
		if ( false !== $i && $i > 0 && wpu_bt_textish_key( $path[ $i - 1 ] ) && in_array( $k, array( 'value', 'text' ), true ) ) {
			$is_text = true;
		}
	}
	if ( $is_text && ! preg_match( '/^(https?:|mailto:|tel:|#|\/)\S*$/', trim( $v ) ) ) {
		$fn( $v, implode( '.', $here ) );
	}
}

/** Raw stored meta value (serialized string as in the database), or null. For exact undo. */
function wpu_bt_meta_raw( $id, $key ) {
	global $wpdb;
	// Fixed table name from $wpdb; values are prepared.
	return $wpdb->get_var( $wpdb->prepare( "SELECT meta_value FROM {$wpdb->postmeta} WHERE post_id = %d AND meta_key = %s ORDER BY meta_id ASC LIMIT 1", $id, $key ) ); // phpcs:ignore WordPress.DB.DirectDatabaseQuery
}

/** Put a raw meta value back exactly (no slashing or re-serializing). */
function wpu_bt_meta_raw_restore( $id, $key, $raw ) {
	global $wpdb;
	if ( null === $raw ) {
		delete_post_meta( $id, $key );
	} elseif ( null === wpu_bt_meta_raw( $id, $key ) ) {
		$wpdb->insert( $wpdb->postmeta, array( 'post_id' => $id, 'meta_key' => $key, 'meta_value' => $raw ) ); // phpcs:ignore WordPress.DB.DirectDatabaseQuery,WordPress.DB.SlowDBQuery
	} else {
		$wpdb->update( $wpdb->postmeta, array( 'meta_value' => $raw ), array( 'post_id' => $id, 'meta_key' => $key ) ); // phpcs:ignore WordPress.DB.DirectDatabaseQuery,WordPress.DB.SlowDBQuery
	}
	wp_cache_delete( $id, 'post_meta' );
}

/** update_post_meta() unslashes what it is given; slash every string inside arrays and objects first. */
function wpu_bt_slash_deep( $value ) {
	return map_deep( $value, function ( $v ) {
		return is_string( $v ) ? addslashes( $v ) : $v;
	} );
}

/* -------------------------------------------------------------------------
 * Per-builder readers and writers
 * Each returns array( 'texts' => [...], 'count' => n, 'save' => callable|null, 'undo' => [...] )
 * ---------------------------------------------------------------------- */

/** $find === null: only collect texts. Otherwise replace and count. */
function wpu_bt_pb_process( $id, $builder, $find, $replace ) {
	$texts = array();
	$count = 0;
	$hits  = array();
	$visit = function ( &$s, $where ) use ( $find, $replace, &$texts, &$count, &$hits ) {
		if ( null === $find ) {
			if ( count( $texts ) < 800 ) {
				$texts[] = array( 'where' => $where, 'text' => wpu_bt_trim( trim( preg_replace( '/\s+/', ' ', wp_strip_all_tags( $s ) ) ), 600 ) );
			}
			return;
		}
		$n = 0;
		$s = wpu_bt_replace_in_text( $s, $find, $replace, $n );
		if ( $n ) {
			$count += $n;
			$hits[] = array( 'where' => $where, 'count' => $n );
		}
	};
	$p    = get_post( $id );
	$undo = array();
	$save = null;

	switch ( $builder ) {
		case 'elementor':
			list( $raw, $data ) = wpu_bt_el_data( $id );
			if ( ! $data ) {
				return wpu_bt_err( 'This page has no Elementor data.' );
			}
			wpu_bt_el_walk( $data, function ( &$v, $el, $path ) use ( $visit ) {
				$visit( $v, ( isset( $el['id'] ) ? $el['id'] : '' ) . ':' . $path );
			} );
			$undo[] = array( 'kind' => 'meta_raw', 'id' => $id, 'key' => '_elementor_data', 'raw' => wpu_bt_meta_raw( $id, '_elementor_data' ), 'flush' => 'elementor' );
			$save   = function () use ( $id, $data ) {
				$doc = isset( \Elementor\Plugin::$instance->documents ) ? \Elementor\Plugin::$instance->documents->get( $id, false ) : null;
				if ( $doc && method_exists( $doc, 'save' ) ) {
					$doc->save( array( 'elements' => $data ) );
				} else {
					update_post_meta( $id, '_elementor_data', wp_slash( wp_json_encode( $data ) ) );
				}
			};
			break;

		case 'divi':
			$content = (string) $p->post_content;
			if ( false !== strpos( $content, '<!-- wp:divi/' ) ) {
				// Divi 5: blocks whose text lives in JSON attributes.
				$blocks = parse_blocks( $content );
				$walk   = function ( array &$list ) use ( &$walk, $visit ) {
					foreach ( $list as &$b ) {
						if ( ! empty( $b['blockName'] ) && 0 === strpos( $b['blockName'], 'divi/' ) && ! empty( $b['attrs'] ) ) {
							$name = $b['blockName'];
							wpu_bt_walk_text( $b['attrs'], function ( &$s, $path ) use ( $visit, $name ) {
								$visit( $s, $name . ':' . $path );
							} );
						}
						if ( ! empty( $b['innerBlocks'] ) ) {
							$walk( $b['innerBlocks'] );
						}
					}
					unset( $b );
				};
				$walk( $blocks );
				$new = serialize_blocks( $blocks );
			} else {
				// Divi 4: shortcodes. Text between tags, plus text attributes such as button_text="...".
				$parts = wpu_bt_split_markup( $content, '\[[^\[\]]*\]' );
				foreach ( $parts as $i => &$part ) {
					if ( 0 === $i % 2 ) {
						if ( '' !== trim( $part ) && preg_match( '/\pL/u', $part ) ) {
							$visit( $part, 'content' );
						}
						continue;
					}
					if ( '[' === $part[0] && preg_match( '/^\[(et_pb_[a-z0-9_]+)/', $part, $m ) ) {
						$tag  = $m[1];
						$part = preg_replace_callback( '/\b([a-z0-9_]+)="([^"]*)"/', function ( $a ) use ( $visit, $tag ) {
							if ( ! wpu_bt_textish_key( $a[1] ) || ! preg_match( '/\pL/u', $a[2] ) ) {
								return $a[0];
							}
							$v = $a[2];
							$visit( $v, $tag . '.' . $a[1] );
							return $a[1] . '="' . $v . '"';
						}, $part );
					}
				}
				unset( $part );
				$new = implode( '', $parts );
			}
			$undo[] = array( 'kind' => 'post', 'id' => $id, 'fields' => array( 'post_content' => $content ) );
			$save   = function () use ( $id, $new ) {
				kses_remove_filters(); // Divi markup is saved as Divi wrote it; the replacement text was filtered already
				try {
					wp_update_post( wp_slash( array( 'ID' => $id, 'post_content' => $new ) ) );
				} finally {
					kses_init(); // always back to the normal rule for this user
				}
				if ( class_exists( 'ET_Core_PageResource' ) && method_exists( 'ET_Core_PageResource', 'remove_static_resources' ) ) {
					ET_Core_PageResource::remove_static_resources( $id, 'all' );
				}
			};
			break;

		case 'bricks':
			$keys = array( '_bricks_page_content_2', '_bricks_page_header_2', '_bricks_page_footer_2' );
			$data = array();
			foreach ( $keys as $key ) {
				$v = get_post_meta( $id, $key, true );
				if ( is_array( $v ) && $v ) {
					foreach ( $v as $i => &$el ) {
						if ( isset( $el['settings'] ) && is_array( $el['settings'] ) ) {
							$label = ( isset( $el['name'] ) ? $el['name'] : 'element' ) . '#' . ( isset( $el['id'] ) ? $el['id'] : $i );
							wpu_bt_walk_text( $el['settings'], function ( &$s, $path ) use ( $visit, $label ) {
								$visit( $s, $label . ':' . $path );
							} );
						}
					}
					unset( $el );
					$data[ $key ] = $v;
					$undo[]       = array( 'kind' => 'meta_raw', 'id' => $id, 'key' => $key, 'raw' => wpu_bt_meta_raw( $id, $key ), 'flush' => 'bricks' );
				}
			}
			if ( ! $data ) {
				return wpu_bt_err( 'This page has no Bricks data.' );
			}
			$save = function () use ( $id, $data ) {
				foreach ( $data as $key => $v ) {
					update_post_meta( $id, $key, wpu_bt_slash_deep( $v ) );
				}
				wpu_bt_pb_flush( $id, 'bricks' );
			};
			break;

		case 'beaver_builder':
			$data = array();
			foreach ( array( '_fl_builder_data', '_fl_builder_draft' ) as $key ) {
				$v = get_post_meta( $id, $key, true );
				if ( ( is_array( $v ) || is_object( $v ) ) && $v ) {
					foreach ( $v as $node_id => $node ) {
						if ( is_object( $node ) && isset( $node->settings ) && is_object( $node->settings ) ) {
							$label    = ( isset( $node->settings->type ) ? $node->settings->type : ( isset( $node->type ) ? $node->type : 'node' ) ) . '#' . $node_id;
							$settings = $node->settings;
							wpu_bt_walk_text( $settings, function ( &$s, $path ) use ( $visit, $label, $key ) {
								$visit( $s, ( '_fl_builder_draft' === $key ? 'draft:' : '' ) . $label . ':' . $path );
							} );
							$node->settings = $settings;
						}
					}
					$data[ $key ] = $v;
					$undo[]       = array( 'kind' => 'meta_raw', 'id' => $id, 'key' => $key, 'raw' => wpu_bt_meta_raw( $id, $key ), 'flush' => 'beaver' );
				}
			}
			if ( ! $data ) {
				return wpu_bt_err( 'This page has no Beaver Builder data.' );
			}
			// Beaver Builder also keeps a rendered copy in post_content (for search engines and when it is off).
			$content = (string) $p->post_content;
			$rendered = $content;
			if ( null !== $find ) {
				list( $rendered ) = wpu_bt_replace_outside_comments( $content, $find, $replace, 1000 );
			}
			$undo[] = array( 'kind' => 'post', 'id' => $id, 'fields' => array( 'post_content' => $content ) );
			$save   = function () use ( $id, $data, $rendered, $content ) {
				foreach ( $data as $key => $v ) {
					update_post_meta( $id, $key, wpu_bt_slash_deep( $v ) );
				}
				if ( $rendered !== $content ) {
					kses_remove_filters();
					try {
						wp_update_post( wp_slash( array( 'ID' => $id, 'post_content' => $rendered ) ) );
					} finally {
						kses_init(); // always back to the normal rule for this user
					}
				}
				wpu_bt_pb_flush( $id, 'beaver' );
			};
			break;

		case 'breakdance':
			$raw_meta = get_post_meta( $id, '_breakdance_data', true );
			$outer    = is_string( $raw_meta ) ? json_decode( $raw_meta, true ) : ( is_array( $raw_meta ) ? $raw_meta : null );
			$tree     = is_array( $outer ) && isset( $outer['tree_json_string'] ) && is_string( $outer['tree_json_string'] ) ? json_decode( $outer['tree_json_string'], true ) : null;
			if ( ! is_array( $tree ) ) {
				return wpu_bt_err( 'This page has no readable Breakdance data.' );
			}
			$walk = function ( array &$node ) use ( &$walk, $visit ) {
				if ( isset( $node['data']['properties'] ) && is_array( $node['data']['properties'] ) ) {
					$type  = isset( $node['data']['type'] ) ? preg_replace( '/^.*\\\\/', '', (string) $node['data']['type'] ) : 'element';
					$label = $type . '#' . ( isset( $node['id'] ) ? $node['id'] : '' );
					// Only content properties: design settings never hold visible text.
					if ( isset( $node['data']['properties']['content'] ) && is_array( $node['data']['properties']['content'] ) ) {
						wpu_bt_walk_text( $node['data']['properties']['content'], function ( &$s, $path ) use ( $visit, $label ) {
							$visit( $s, $label . ':content.' . $path );
						} );
					}
				}
				if ( ! empty( $node['children'] ) && is_array( $node['children'] ) ) {
					foreach ( $node['children'] as &$c ) {
						if ( is_array( $c ) ) {
							$walk( $c );
						}
					}
					unset( $c );
				}
			};
			if ( isset( $tree['root'] ) && is_array( $tree['root'] ) ) {
				$walk( $tree['root'] );
			}
			$outer['tree_json_string'] = wp_json_encode( $tree, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE );
			$undo[]                    = array( 'kind' => 'meta_raw', 'id' => $id, 'key' => '_breakdance_data', 'raw' => wpu_bt_meta_raw( $id, '_breakdance_data' ), 'flush' => 'breakdance' );
			$save                      = function () use ( $id, $outer, $raw_meta ) {
				$value = is_string( $raw_meta ) ? wp_slash( wp_json_encode( $outer, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE ) ) : wpu_bt_slash_deep( $outer );
				update_post_meta( $id, '_breakdance_data', $value );
				wpu_bt_pb_flush( $id, 'breakdance' );
			};
			break;

		case 'seedprod':
			$json = json_decode( (string) $p->post_content_filtered, true );
			if ( ! is_array( $json ) ) {
				return wpu_bt_err( 'This page has no readable SeedProd data.' );
			}
			wpu_bt_walk_text( $json, function ( &$s, $path ) use ( $visit ) {
				$visit( $s, $path );
			} );
			$content  = (string) $p->post_content;
			$rendered = $content;
			if ( null !== $find ) {
				list( $rendered ) = wpu_bt_replace_outside_comments( $content, $find, $replace, 1000 );
			}
			$undo[] = array( 'kind' => 'post', 'id' => $id, 'fields' => array( 'post_content' => $content, 'post_content_filtered' => $p->post_content_filtered ) );
			$save   = function () use ( $id, $json, $rendered ) {
				kses_remove_filters();
				try {
					wp_update_post( wp_slash( array( 'ID' => $id, 'post_content' => $rendered, 'post_content_filtered' => wp_json_encode( $json, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE ) ) ) );
				} finally {
					kses_init(); // always back to the normal rule for this user
				}
				wpu_bt_pb_flush( $id, 'seedprod' );
			};
			break;

		default: // gutenberg, classic, empty
			$content = (string) $p->post_content;
			$new     = $content;
			if ( null === $find ) {
				$parts = wpu_bt_split_markup( $content );
				foreach ( $parts as $i => $part ) {
					if ( 0 === $i % 2 && '' !== trim( $part ) && preg_match( '/\pL/u', $part ) ) {
						$visit( $part, 'content' );
					}
				}
			}
			if ( null !== $find ) {
				list( $new, $count ) = wpu_bt_replace_outside_comments( $content, $find, $replace, 1000 );
				$hits                = $count ? array( array( 'where' => 'content', 'count' => $count ) ) : array();
			}
			$undo[] = array( 'kind' => 'post', 'id' => $id, 'fields' => array( 'post_content' => $content ) );
			$save   = function () use ( $id, $new ) {
				wp_update_post( wp_slash( array( 'ID' => $id, 'post_content' => $new ) ) );
				wpu_bt_after_content_write( $id );
			};
	}
	return array( 'texts' => $texts, 'count' => $count, 'hits' => $hits, 'save' => $save, 'undo' => $undo );
}

/** Clear a builder's generated CSS/cache for one page so the change shows. */
function wpu_bt_pb_flush( $id, $builder ) {
	switch ( $builder ) {
		case 'elementor':
			wpu_bt_elementor_flush( $id );
			break;
		case 'bricks':
			if ( class_exists( '\Bricks\Assets' ) && method_exists( '\Bricks\Assets', 'generate_css_file' ) ) {
				try {
					\Bricks\Assets::generate_css_file( $id );
				} catch ( Throwable $e ) {
					unset( $e ); // the page still renders; Bricks rebuilds its CSS on the next save
				}
			}
			break;
		case 'beaver':
			if ( class_exists( 'FLBuilderModel' ) && method_exists( 'FLBuilderModel', 'delete_all_asset_cache' ) ) {
				FLBuilderModel::delete_all_asset_cache( $id );
			}
			break;
		case 'breakdance':
			foreach ( array_keys( (array) get_post_meta( $id ) ) as $k ) {
				if ( 0 === strpos( $k, '_breakdance_css' ) ) {
					delete_post_meta( $id, $k );
				}
			}
			break;
	}
	clean_post_cache( $id );
	do_action( 'litespeed_purge_post', $id );
	if ( function_exists( 'rocket_clean_post' ) ) {
		rocket_clean_post( $id );
	}
}

/** After Gutenberg content changes: let Spectra rebuild its per-page CSS, clear page caches. */
function wpu_bt_after_content_write( $id ) {
	if ( defined( 'UAGB_VER' ) ) {
		delete_post_meta( $id, '_uag_page_assets' );
		delete_post_meta( $id, '_uag_css_file_name' );
		delete_post_meta( $id, '_uag_js_file_name' );
	}
	clean_post_cache( $id );
	do_action( 'litespeed_purge_post', $id );
	if ( function_exists( 'rocket_clean_post' ) ) {
		rocket_clean_post( $id );
	}
}

/** Block plugins used on a Gutenberg page (kadence, uagb = Spectra, generateblocks, ...). */
function wpu_bt_block_namespaces( $content ) {
	preg_match_all( '/<!--\s+wp:([a-z0-9-]+)\//', (string) $content, $m );
	return array_values( array_diff( array_unique( $m[1] ), array( 'core' ) ) );
}

/* -------------------------------------------------------------------------
 * Tools
 * ---------------------------------------------------------------------- */

wpu_bt_define_tool( 'builder_page_text', array(
	'title'       => 'Page text (any builder)',
	'description' => 'Every piece of visible text on a page, whatever it was built with: Gutenberg (including Kadence and Spectra blocks), classic editor, Elementor, Divi 4 and 5, Bricks, Beaver Builder, Breakdance or SeedProd. Each text has a location.',
	'cap'         => 'edit_posts',
	'props'       => array( 'id' => array( 'type' => 'integer' ) ),
	'required'    => array( 'id' ),
	'run'         => function ( $a ) {
		$id = absint( $a['id'] );
		if ( ! get_post( $id ) || ! current_user_can( 'edit_post', $id ) ) {
			return wpu_bt_err( 'No post ' . $id . ' that you can edit.' );
		}
		$builder = wpu_bt_post_builder( $id );
		$r       = wpu_bt_pb_process( $id, $builder, null, null );
		if ( is_wp_error( $r ) ) {
			return $r;
		}
		$out = array( 'id' => $id, 'title' => get_the_title( $id ), 'builder' => $builder, 'texts' => $r['texts'] );
		if ( 'gutenberg' === $builder ) {
			$out['block_plugins'] = wpu_bt_block_namespaces( get_post_field( 'post_content', $id ) );
		}
		return $out;
	},
) );

wpu_bt_define_tool( 'builder_replace_text', array(
	'title'       => 'Change page text (any builder)',
	'description' => 'Find and replace visible text on one page in whichever builder made it (Gutenberg, Kadence, Spectra, classic, Elementor, Divi 4/5, Bricks, Beaver Builder, Breakdance, SeedProd). Exact and case-sensitive. Never changes styling, links, ids or HTML tags. dry_run shows where it matches. Clears the builder\'s cache and returns a change_id for undo.',
	'cap'         => 'edit_posts',
	'props'       => array(
		'id'      => array( 'type' => 'integer' ),
		'find'    => array( 'type' => 'string' ),
		'replace' => array( 'type' => 'string' ),
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
		if ( '' === trim( $find ) ) {
			return wpu_bt_err( 'find is empty.' );
		}
		$builder = wpu_bt_post_builder( $id );
		if ( 'divi' === $builder && preg_match( '/["\'\[\]<>]/', $find . $replace ) ) {
			return wpu_bt_err( 'For Divi pages, find and replace cannot contain quotes, [ ] or < > (they would break Divi\'s shortcodes).' );
		}
		$r = wpu_bt_pb_process( $id, $builder, $find, $replace );
		if ( is_wp_error( $r ) ) {
			return $r;
		}
		if ( ! $r['count'] ) {
			return array( 'builder' => $builder, 'replaced' => 0, 'note' => 'Text not found. Check spelling and spaces with builder_page_text.' );
		}
		if ( wpu_bt_bool( $a, 'dry_run' ) ) {
			return array( 'dry_run' => true, 'builder' => $builder, 'would_replace' => $r['count'], 'where' => $r['hits'] );
		}
		call_user_func( $r['save'] );
		$cid = wpu_bt_change_add( 'builder_replace_text', ucfirst( $builder ) . ' text on #' . $id . ': "' . substr( $find, 0, 40 ) . '" -> "' . substr( $replace, 0, 40 ) . '" (' . $r['count'] . 'x)', array( 'kind' => 'multi', 'items' => $r['undo'] ) );
		return array( 'builder' => $builder, 'replaced' => $r['count'], 'where' => $r['hits'], 'url' => get_permalink( $id ), 'change_id' => $cid );
	},
) );
