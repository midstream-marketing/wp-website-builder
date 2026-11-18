<?php
/**
 * Divi layout building (Divi 4 format: the Divi theme, Extra, or the Divi Builder plugin, version 4.x).
 *
 * Claude sends a layout as a typed tree - sections > rows > columns > modules (> child items) - and this
 * file checks it against Divi's own module registry on the site, then writes Divi's shortcodes. Nothing is
 * taken on trust: module names, where each may sit, column structures, setting names and values are all
 * validated, and the Code modules (which hold raw HTML and script) are refused.
 *
 * Existing Divi pages can be read as an outline and edited by path (change settings or content, insert,
 * remove, move, duplicate). Parts of a page that an edit does not touch are kept byte for byte.
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/** Modules that hold raw HTML/JS, or run things: never written by the bridge. */
const WPU_BT_DIVI_REFUSED = array( 'et_pb_code', 'et_pb_fullwidth_code' );

function wpu_bt_has_divi() {
	return defined( 'ET_BUILDER_VERSION' ) && defined( 'ET_BUILDER_DIR' );
}

/** True when the site runs Divi 4.x (shortcode format). Divi 5 stores pages as blocks. */
function wpu_bt_divi_is_v4() {
	$v = defined( 'ET_BUILDER_PRODUCT_VERSION' ) ? ET_BUILDER_PRODUCT_VERSION : ( defined( 'ET_BUILDER_VERSION' ) ? ET_BUILDER_VERSION : '0' );
	return version_compare( $v, '5.0', '<' );
}

/**
 * Load Divi's module classes. Divi only loads them on front-end page views and its own screens, not for
 * REST requests like ours, so load the same files Divi loads itself. Returns '' or the reason it failed.
 */
function wpu_bt_divi_boot() {
	static $state = null;
	if ( null !== $state ) {
		return $state;
	}
	if ( ! wpu_bt_has_divi() ) {
		$state = 'Divi is not active on this site.';
		return $state;
	}
	try {
		// Divi 5 keeps the Divi 4 module classes for old content and loads them on demand.
		if ( function_exists( 'et_load_shortcode_framework' ) && function_exists( 'et_is_shortcode_framework_loaded' ) && ! et_is_shortcode_framework_loaded() ) {
			et_load_shortcode_framework();
		}
		if ( ! class_exists( 'ET_Builder_Element' ) ) {
			foreach ( array( 'functions.php', 'class-et-global-settings.php', 'class-et-builder-value.php', 'class-et-builder-element.php', 'class-et-builder-plugin-compat-base.php', 'class-et-builder-plugin-compat-loader.php', 'class-et-builder-theme-compat-base.php', 'class-et-builder-theme-compat-handler.php', 'ab-testing.php', 'class-et-builder-settings.php', 'class-et-builder-post-feature-base.php', 'class-et-builder-global-feature-base.php', 'class-et-builder-module-features.php', 'class-et-builder-google-fonts-feature.php', 'class-et-builder-dynamic-assets-feature.php', 'class-et-builder-module-shortcode-manager.php' ) as $f ) {
				if ( is_file( ET_BUILDER_DIR . $f ) ) {
					require_once ET_BUILDER_DIR . $f;
				}
			}
		}
		if ( ! did_action( 'et_builder_ready' ) ) {
			if ( function_exists( 'et_builder_init_global_settings' ) ) {
				et_builder_init_global_settings();
			}
			if ( function_exists( 'et_builder_add_main_elements' ) ) {
				et_builder_add_main_elements();
			}
		}
		$state = class_exists( 'ET_Builder_Element' ) && wpu_bt_divi_load( 'et_pb_text' ) ? '' : 'Divi\'s modules could not be loaded.';
	} catch ( Throwable $e ) {
		$state = 'Divi\'s modules could not be loaded.';
	}
	return $state;
}

/**
 * Divi loads a module's class only when a page uses it. Ask Divi's own loader for the one we need.
 * $tag null loads every module Divi ships (for the list). Returns the module object, or null.
 */
function wpu_bt_divi_load( $tag ) {
	static $manager = null, $all = false;
	if ( ! class_exists( 'ET_Builder_Element' ) ) {
		return null;
	}
	if ( class_exists( 'ET_Builder_Module_Shortcode_Manager' ) && method_exists( 'ET_Builder_Module_Shortcode_Manager', 'maybe_load_module_from_slug' ) ) {
		if ( null === $manager ) {
			$manager = new ET_Builder_Module_Shortcode_Manager(); // the module map is static; init() already ran
		}
		try {
			if ( null === $tag ) {
				if ( ! $all ) {
					$all = true;
					foreach ( array( false, 'woo_modules' ) as $type ) {
						if ( 'woo_modules' === $type && ! class_exists( 'WooCommerce' ) ) {
							continue;
						}
						foreach ( array_keys( (array) ET_Builder_Module_Shortcode_Manager::get_modules_map( $type ) ) as $slug ) {
							$manager->maybe_load_module_from_slug( $slug );
						}
					}
				}
			} elseif ( ! ET_Builder_Element::get_module( $tag, 'page' ) ) {
				$manager->maybe_load_module_from_slug( $tag );
			}
		} catch ( Throwable $e ) {
			return null;
		}
	}
	return null === $tag ? null : ET_Builder_Element::get_module( $tag, 'page' );
}

/** Divi module object for a tag, or null. */
function wpu_bt_divi_module( $tag ) {
	return '' === wpu_bt_divi_boot() ? wpu_bt_divi_load( $tag ) : null;
}

function wpu_bt_divi_tag( $type ) {
	$t = strtolower( trim( (string) $type ) );
	if ( ! preg_match( '/^[a-z0-9_]{2,60}\z/', $t ) ) {
		return '';
	}
	if ( 0 === strpos( $t, 'et_pb_' ) ) {
		return $t;
	}
	// Modules from other plugins keep their own prefix; Divi's own may be given without "et_pb_".
	return wpu_bt_divi_is_tag( $t ) ? $t : 'et_pb_' . $t;
}

/** Is this shortcode tag a Divi element on this site (Divi's own or one registered by another plugin)? */
function wpu_bt_divi_is_tag( $tag ) {
	static $extra = null;
	if ( 0 === strpos( $tag, 'et_pb_' ) ) {
		return true;
	}
	if ( null === $extra ) {
		$extra = array();
		if ( '' === wpu_bt_divi_boot() ) {
			wpu_bt_divi_load( null );
			$extra = array_fill_keys( array_keys( (array) ET_Builder_Element::get_parent_and_child_modules( 'page' ) ), true );
		}
	}
	return isset( $extra[ $tag ] );
}

/**
 * What a stored value can turn into once Divi and WordPress have decoded it: Divi's own escapes (%22 %91 %93
 * %92), HTML entities and percent-encoding, repeated until nothing changes. Checks run on this form, because
 * Divi decodes some settings and then runs shortcodes in them.
 */
function wpu_bt_divi_canon( $text ) {
	$text = (string) $text;
	for ( $i = 0; $i < 6; $i++ ) {
		$divi = array( array( '%22', '%91', '%93', '%92' ), array( '"', '[', ']', '\\' ) );
		$next = str_ireplace( $divi[0], $divi[1], $text );
		$next = html_entity_decode( $next, ENT_QUOTES | ENT_HTML5, 'UTF-8' );
		$next = str_ireplace( $divi[0], $divi[1], $next ); // an entity may have spelled out a Divi escape
		$next = rawurldecode( $next );
		if ( $next === $text ) {
			break;
		}
		$text = $next;
	}
	return $text;
}

/** Does text contain (in any encoded form) the opening or closing tag of any Divi element? */
function wpu_bt_divi_has_tag( $text ) {
	$text = wpu_bt_divi_canon( $text );
	if ( false === strpos( $text, '[' ) || ! preg_match_all( '/\[[\s\/]*([A-Za-z][A-Za-z0-9_-]*)/', $text, $m ) ) {
		return false;
	}
	foreach ( array_unique( $m[1] ) as $t ) {
		if ( wpu_bt_divi_is_tag( strtolower( $t ) ) ) {
			return true;
		}
	}
	return false;
}

/** Does text contain (in any encoded form) a shortcode registered on this site? */
function wpu_bt_divi_any_shortcode( $text ) {
	foreach ( array( (string) $text, wpu_bt_divi_canon( $text ) ) as $t ) {
		if ( false === strpos( $t, '[' ) || ! preg_match_all( '/\[[\s\/\[]*([^\s\]\/<>&=\[\x00-\x20]+)/', $t, $m ) ) {
			continue;
		}
		foreach ( array_unique( $m[1] ) as $tag ) {
			if ( shortcode_exists( $tag ) || shortcode_exists( strtolower( $tag ) ) ) {
				return true;
			}
		}
	}
	return false;
}

/** Divi dynamic content in any form: its @ET-DC@ wrapper, or the bare JSON Divi also accepts. */
function wpu_bt_divi_is_dynamic( $text ) {
	foreach ( array( (string) $text, wpu_bt_divi_canon( $text ) ) as $t ) {
		// Divi 4's wrapper, and Divi 5's $variable(...)$ token, which Divi 5 resolves in any setting or text.
		if ( false !== stripos( $t, '@ET-DC@' ) || false !== stripos( $t, '$variable(' ) ) {
			return true;
		}
		$t = trim( $t );
		if ( '' !== $t && '{' === $t[0] ) {
			$j = json_decode( $t, true );
			if ( is_array( $j ) && array_key_exists( 'dynamic', $j ) ) {
				return true;
			}
		}
	}
	return false;
}

/**
 * Divi's editor decodes entities in settings and content before showing them. Refuse text whose decoded
 * form holds markup the content filter would not allow (script hidden as &lt;script&gt;, for example).
 */
function wpu_bt_divi_hidden_markup( $text ) {
	$c = wpu_bt_divi_canon( $text );
	return false !== strpos( $c, '<' ) && wpu_bt_divi_canon( wp_kses_post( $c ) ) !== $c;
}

/** A script-capable address hidden in a value, in any encoded form. */
function wpu_bt_divi_bad_scheme( $text ) {
	$c = preg_replace( '/[\x00-\x20\x7f]+/', '', wp_strip_all_tags( wpu_bt_divi_canon( $text ) ) );
	return (bool) preg_match( '/^(javascript|vbscript|data|livescript):/i', $c );
}

/**
 * May the bridge write this module? Divi's own modules: yes, except the Code modules. Modules added by
 * other plugins: only when an administrator switched that on, and never ones that hold raw code.
 * @return true|WP_Error
 */
function wpu_bt_divi_writable( $tag ) {
	if ( in_array( $tag, WPU_BT_DIVI_REFUSED, true ) ) {
		return wpu_bt_err( 'The Code module holds raw HTML and script, so the bridge does not write it. Add it by hand in Divi if it is needed.' );
	}
	if ( in_array( $tag, array( 'et_pb_section', 'et_pb_row', 'et_pb_column', 'et_pb_row_inner', 'et_pb_column_inner' ), true ) ) {
		return true;
	}
	$shipped = false;
	if ( class_exists( 'ET_Builder_Module_Shortcode_Manager' ) && method_exists( 'ET_Builder_Module_Shortcode_Manager', 'get_modules_map' ) ) {
		foreach ( array( false, 'woo_modules', 'structural_modules' ) as $type ) {
			$map = (array) ET_Builder_Module_Shortcode_Manager::get_modules_map( $type );
			if ( isset( $map[ $tag ] ) ) {
				$shipped = true;
			}
		}
	}
	if ( $shipped ) {
		return true;
	}
	$m = wpu_bt_divi_module( $tag );
	if ( preg_match( '/code|html|script|php|embed|iframe|raw|snippet|inject/i', $tag ) || ( $m && ! empty( $m->use_raw_content ) ) ) {
		return wpu_bt_err( $tag . ' holds raw code, so the bridge does not write it. Add it by hand in Divi.' );
	}
	if ( ! wpu_bt_setting( 'divi_addons' ) ) {
		return wpu_bt_err( $tag . ' comes from another plugin, not Divi itself. An administrator can allow such modules under Tools > WPU Bridge ("Divi modules from other plugins").' );
	}
	return true;
}

/** Does this element or anything inside it fall outside what the bridge may write? */
function wpu_bt_divi_tree_refused( array $node ) {
	if ( is_wp_error( wpu_bt_divi_writable( $node['tag'] ) ) ) {
		return true;
	}
	foreach ( $node['children'] as $c ) {
		if ( wpu_bt_divi_tree_refused( $c ) ) {
			return true;
		}
	}
	return false;
}

function wpu_bt_divi_count( array $nodes ) {
	$n = count( $nodes );
	foreach ( $nodes as $c ) {
		$n += wpu_bt_divi_count( $c['children'] );
	}
	return $n;
}

/** Info about a module tag: kind (structure|module|child), child tag, fullwidth. Null when unknown. */
function wpu_bt_divi_info( $tag ) {
	static $cache = array();
	if ( isset( $cache[ $tag ] ) ) {
		return $cache[ $tag ];
	}
	if ( in_array( $tag, array( 'et_pb_section', 'et_pb_row', 'et_pb_column', 'et_pb_row_inner', 'et_pb_column_inner' ), true ) ) {
		return $cache[ $tag ] = array( 'kind' => 'structure', 'child' => '', 'fullwidth' => false, 'name' => ucfirst( str_replace( array( 'et_pb_', '_' ), array( '', ' ' ), $tag ) ) );
	}
	$m = wpu_bt_divi_module( $tag );
	if ( ! $m ) {
		return $cache[ $tag ] = null;
	}
	return $cache[ $tag ] = array(
		'kind'      => isset( $m->type ) && 'child' === $m->type ? 'child' : 'module',
		'child'     => ! empty( $m->child_slug ) ? (string) $m->child_slug : '',
		'fullwidth' => ! empty( $m->fullwidth ) || 0 === strpos( $tag, 'et_pb_fullwidth_' ),
		'name'      => (string) $m->name,
	);
}

/** Setting names Divi knows for a tag (content, design and advanced tabs). */
function wpu_bt_divi_fields( $tag ) {
	static $cache = array();
	if ( isset( $cache[ $tag ] ) ) {
		return $cache[ $tag ];
	}
	$m = wpu_bt_divi_module( $tag );
	if ( ! $m ) {
		return $cache[ $tag ] = array();
	}
	$fields = array();
	try {
		$fields = (array) $m->get_fields();
		if ( isset( $m->fields_unprocessed ) && is_array( $m->fields_unprocessed ) ) {
			$fields += $m->fields_unprocessed;
		}
		if ( method_exists( $m, 'get_default_props' ) ) {
			$fields += array_fill_keys( array_keys( (array) $m->get_default_props() ), true );
		}
	} catch ( Throwable $e ) {
		$fields = (array) $m->get_fields();
	}
	foreach ( array_keys( $fields ) as $k ) {
		if ( ! preg_match( '/^[a-z][a-z0-9_]*$/', (string) $k ) ) {
			unset( $fields[ $k ] ); // Divi's internal markers
		}
	}
	return $cache[ $tag ] = $fields;
}

/** Setting name without its responsive, hover or sticky ending. */
function wpu_bt_divi_base_name( $name ) {
	return preg_replace( '/(__hover_enabled|__hover|__sticky_enabled|__sticky|_last_edited|_tablet|_phone)\z/', '', (string) $name );
}

/** Is $name a setting Divi accepts on $tag? Handles the responsive, hover and sticky variants. */
function wpu_bt_divi_attr_known( $tag, $name ) {
	static $always = array( 'admin_label', 'module_id', 'module_class', '_builder_version', '_module_preset', 'global_colors_info', 'disabled_on', 'locked', 'collapsed', 'fb_built', 'theme_builder_area', 'type', 'column_structure', 'fullwidth', 'specialty', 'open', 'saved_tabs' );
	if ( in_array( $name, $always, true ) ) {
		return true;
	}
	$fields = wpu_bt_divi_fields( $tag );
	if ( isset( $fields[ $name ] ) ) {
		return true;
	}
	$base = wpu_bt_divi_base_name( $name );
	if ( $base !== $name && ( isset( $fields[ $base ] ) || in_array( $base, $always, true ) ) ) {
		return true;
	}
	// Column-indexed row/section settings: background_color_1, padding_top_2 ...
	$base2 = preg_replace( '/_[1-6]\z/', '', $base );
	if ( $base2 !== $base && isset( $fields[ $base2 ] ) ) {
		return true;
	}
	// Border and shadow settings, which Divi builds only while a page renders.
	return (bool) preg_match( '/^(border_(radii|(width|color|style)_(all|top|right|bottom|left))|box_shadow_(style|horizontal|vertical|blur|spread|color|position))(_[a-z0-9_]{1,40})?\z/', $base );
}

/* -------------------------------------------------------------------------
 * Values: cleaned, then encoded the way Divi stores them
 * ---------------------------------------------------------------------- */

/** @return string|WP_Error encoded attribute value */
function wpu_bt_divi_attr_value( $tag, $name, $value ) {
	if ( is_bool( $value ) ) {
		$value = $value ? 'on' : 'off';
	}
	if ( is_array( $value ) ) {
		return wpu_bt_err( 'Setting ' . $name . ' on ' . $tag . ' must be text or a number.' );
	}
	$v = (string) $value;
	if ( strlen( $v ) > 20000 ) {
		return wpu_bt_err( 'Setting ' . $name . ' is too long.' );
	}
	$base   = wpu_bt_divi_base_name( $name );
	$base   = preg_replace( '/_[1-6]\z/', '', $base );
	$fields = wpu_bt_divi_fields( $tag );
	$def    = isset( $fields[ $base ] ) && is_array( $fields[ $base ] ) ? $fields[ $base ] : array();
	$is_url = ( isset( $def['type'] ) && 'upload' === $def['type'] )
		|| ( preg_match( '/(^|_)(url|src|href)(_|\z)|(^|_)link\z|(^|_)(image|logo|video|audio|mp4|webm)\z/', $base ) && ! preg_match( '/(_new_window|_target|_rel)\z/', $base ) );
	if ( preg_match( '/_last_edited\z|_enabled\z/', $name ) ) {
		$is_url = false; // "on|tablet" style switches
	}
	if ( 0 === strpos( $name, 'custom_css' ) ) {
		if ( preg_match( '/<|expression\s*\(|javascript\s*:|behavior\s*:|-moz-binding|@import/i', wpu_bt_divi_canon( $v ) ) ) {
			return wpu_bt_err( 'CSS in ' . $name . ' may not contain "<", @import, javascript: or expression().' );
		}
		if ( 'custom_css_free_form' !== wpu_bt_divi_base_name( $name ) && preg_match( '/[{}]/', wpu_bt_divi_canon( $v ) ) ) {
			return wpu_bt_err( 'CSS in ' . $name . ' is a list of declarations (color: red;), without { or }.' );
		}
	} elseif ( $is_url ) {
		$t = trim( $v );
		if ( '' !== $t && '#' === $t[0] ) {
			$v = '#' . preg_replace( '/[^A-Za-z0-9_-]/', '', substr( $t, 1 ) );
		} elseif ( '' !== $t ) {
			$v = esc_url_raw( $t, array( 'http', 'https', 'mailto', 'tel' ) );
			if ( '' === $v ) {
				return wpu_bt_err( 'Setting ' . $name . ' must be a web address (http, https, mailto or tel).' );
			}
		}
	} else {
		$v = wp_kses_post( $v );
	}
	// Option lists and field rules are JSON that Divi decodes itself: check what is inside.
	if ( preg_match( '/(^|_)(checkbox|radio|select|booleancheckbox)_options\z|(^|_)conditional_logic_rules\z/', $base ) ) {
		$list = json_decode( wpu_bt_divi_canon( $v ), true );
		if ( ! is_array( $list ) || ( $list && array_keys( $list ) !== range( 0, count( $list ) - 1 ) ) || count( $list ) > 200 ) {
			return wpu_bt_err( 'Setting ' . $name . ' must be a JSON list of options.' );
		}
		foreach ( $list as $item ) {
			if ( ! is_array( $item ) ) {
				return wpu_bt_err( 'Setting ' . $name . ' must be a JSON list of option objects.' );
			}
			foreach ( $item as $key => $leaf ) {
				if ( ! in_array( (string) $key, array( 'value', 'checked', 'dragID', 'link_url', 'link_text', 'field', 'condition', 'id' ), true ) ) {
					return wpu_bt_err( 'Setting ' . $name . ': unknown option key. Use value, checked, link_url, link_text (or field, condition, value for rules).' );
				}
				if ( is_array( $leaf ) || is_object( $leaf ) ) {
					return wpu_bt_err( 'Setting ' . $name . ': each option value must be plain text or a number.' );
				}
				$leaf = (string) $leaf;
				if ( false !== strpos( $leaf, '<' ) || false !== strpos( $leaf, '$variable(' ) || wpu_bt_divi_bad_scheme( $leaf ) || preg_match( '/(javascript|vbscript|data)\s*:/i', $leaf ) ) {
					return wpu_bt_err( 'Setting ' . $name . ': options may not hold markup or script addresses.' );
				}
			}
		}
	}
	// Everything below is checked after filtering, on the decoded form: filtering can itself join pieces together.
	if ( wpu_bt_divi_is_dynamic( $v ) ) {
		return wpu_bt_err( 'Setting ' . $name . ' holds Divi dynamic content, which is set in Divi itself.' );
	}
	if ( preg_match( '/%9[13]/', $v ) ) {
		return wpu_bt_err( 'Setting ' . $name . ' may not contain %91 or %93.' );
	}
	if ( 0 !== strpos( $name, 'custom_css' ) && wpu_bt_divi_hidden_markup( $v ) ) {
		return wpu_bt_err( 'Setting ' . $name . ' holds encoded markup that is not allowed.' );
	}
	if ( wpu_bt_divi_bad_scheme( $v ) ) {
		return wpu_bt_err( 'Setting ' . $name . ' may not hold a javascript: or data: address.' );
	}
	if ( wpu_bt_divi_has_tag( $v ) ) {
		return wpu_bt_err( 'Setting ' . $name . ' may not contain Divi shortcodes.' );
	}
	// Divi runs shortcodes inside the tablet, phone and hover versions of these: no brackets there at all.
	if ( $base !== $name && in_array( $base, array( 'content', 'raw_content', 'description', 'footer_content' ), true ) && preg_match( '/[\[\]]/', wpu_bt_divi_canon( $v ) ) ) {
		return wpu_bt_err( 'Setting ' . $name . ' may not contain square brackets.' );
	}
	// Divi's own escapes for characters that would end the attribute or the shortcode.
	return str_replace( array( '\\', '"', '[', ']' ), array( '%92', '%22', '%91', '%93' ), $v );
}

/** Module content (HTML). @return string|WP_Error */
function wpu_bt_divi_content( $html, $tag = '' ) {
	$html = wp_kses_post( (string) $html );
	if ( wpu_bt_divi_has_tag( $html ) ) {
		return wpu_bt_err( 'Content may not contain Divi shortcodes; use child items or separate modules.' );
	}
	if ( wpu_bt_divi_is_dynamic( $html ) ) {
		return wpu_bt_err( 'Content may not be Divi dynamic content; that is set in Divi itself.' );
	}
	// Divi's editor decodes entities in the content of modules it cannot edit visually; for those, escaped
	// markup must itself be allowed markup. Modules with full editor support show escaped text as text.
	$m      = '' === $tag ? null : wpu_bt_divi_module( $tag );
	$strict = ! $m || ! isset( $m->vb_support ) || 'on' !== $m->vb_support;
	if ( preg_match( '/%9[13]/', $html ) || ( $strict && wpu_bt_divi_hidden_markup( $html ) ) ) {
		return wpu_bt_err( 'Content holds encoded markup that is not allowed.' );
	}
	if ( function_exists( 'wpu_bt_divi_is_v5' ) && wpu_bt_divi_is_v5() ) {
		// Divi 5 runs shortcodes in content and then reads the result again for its own tokens, and it
		// turns %22 and %92 back into quotes and backslashes after the content filter has run.
		if ( wpu_bt_divi_any_shortcode( $html ) ) {
			return wpu_bt_err( 'On Divi 5, content may not contain shortcodes. Add the shortcode in Divi itself.' );
		}
		if ( preg_match( '/%(22|92|5c)/i', $html ) ) {
			return wpu_bt_err( 'Content holds encoded quotes or backslashes (%22, %92, %5c), which Divi 5 would decode after filtering.' );
		}
	}
	return $html;
}

/* -------------------------------------------------------------------------
 * Layout tree -> validated nodes -> shortcodes
 *
 * A node is array( 'tag', 'attrs' => name => encoded value, 'children' => nodes, 'content' => html,
 * 'raw_open' => original opening tag when parsed from a page and not changed since ).
 * ---------------------------------------------------------------------- */

function wpu_bt_divi_attrs( $tag, $attrs, &$warnings ) {
	$out = array();
	foreach ( (array) $attrs as $k => $v ) {
		$k = (string) $k;
		if ( ! preg_match( '/^[a-z0-9_]{1,80}\z/', $k ) ) {
			return wpu_bt_err( 'Setting name "' . $k . '" is not valid.' );
		}
		if ( in_array( $k, array( 'fb_built', '_builder_version', 'global_module', 'saved_tabs', 'global_parent', 'template_type', 'theme_builder_area', '_dynamic_attributes', 'ab_subject', 'ab_subject_id', 'ab_goal', 'global_colors_info' ), true ) || 0 === strpos( $k, 'display_conditions' ) ) {
			continue; // set by the bridge, or tied to Divi's library
		}
		if ( ! wpu_bt_divi_attr_known( $tag, $k ) ) {
			$warnings[] = $tag . ': Divi has no setting called "' . $k . '" - left out.';
			continue;
		}
		if ( null === $v ) {
			continue;
		}
		$clean = wpu_bt_divi_attr_value( $tag, $k, $v );
		if ( is_wp_error( $clean ) ) {
			return $clean;
		}
		if ( in_array( $tag, array( 'et_pb_contact_form', 'et_pb_signup' ), true ) && in_array( $k, array( 'email', 'redirect_url', 'use_redirect' ), true ) ) {
			$warnings[] = 'A form\'s recipient or redirect was set (' . $k . '). Ask the person to confirm it before the page is published.';
		}
		$out[ $k ] = $clean;
	}
	return $out;
}

/** Column widths like "1_2,1_2" must be Divi fractions that add up to one row. */
function wpu_bt_divi_structure( $s ) {
	$parts = array_map( 'trim', explode( ',', (string) $s ) );
	$sum   = 0;
	foreach ( $parts as $p ) {
		if ( ! in_array( $p, array( '4_4', '1_2', '1_3', '2_3', '1_4', '3_4', '1_5', '2_5', '3_5', '4_5', '1_6', '5_6' ), true ) ) {
			return wpu_bt_err( 'Column width "' . sanitize_text_field( $p ) . '" is not a Divi width (use 4_4, 1_2, 1_3, 2_3, 1_4, 3_4, 1_5, 2_5, 3_5, 1_6, 5_6).' );
		}
		$sum += (int) $p[0] / (int) $p[2];
	}
	if ( count( $parts ) > 6 || abs( $sum - 1 ) > 0.001 ) {
		return wpu_bt_err( 'Columns "' . sanitize_text_field( (string) $s ) . '" must add up to one full row (for example 1_2,1_2 or 1_4,3_4).' );
	}
	return $parts;
}

/** Refuse keys a node does not take, so a misplaced node is an error and not silently something else. */
function wpu_bt_divi_keys( $in, array $allowed, $what ) {
	if ( ! is_array( $in ) && ! is_object( $in ) ) {
		return wpu_bt_err( 'A ' . $what . ' must be an object.' );
	}
	$extra = array_diff( array_map( 'strval', array_keys( (array) $in ) ), $allowed );
	if ( $extra ) {
		return wpu_bt_err( 'A ' . $what . ' takes ' . implode( ', ', $allowed ) . ' - not "' . sanitize_text_field( (string) reset( $extra ) ) . '".' );
	}
	return true;
}

/** One module (or child item) from input. */
function wpu_bt_divi_module_node( $in, $fullwidth_section, &$warnings, $child_of = '' ) {
	$ok = wpu_bt_divi_keys( $in, array( 'type', 'attrs', 'content', 'children' ), 'module' );
	if ( is_wp_error( $ok ) ) {
		return $ok;
	}
	$in  = (array) $in;
	$tag = wpu_bt_divi_tag( isset( $in['type'] ) ? $in['type'] : '' );
	if ( '' !== $child_of && '' === $tag ) {
		$tag = $child_of;
	}
	$info = '' === $tag ? null : wpu_bt_divi_info( $tag );
	if ( ! $info || 'structure' === $info['kind'] ) {
		return wpu_bt_err( 'Unknown Divi module "' . ( isset( $in['type'] ) ? sanitize_text_field( (string) $in['type'] ) : '' ) . '". See divi_modules.' );
	}
	$can = wpu_bt_divi_writable( $tag );
	if ( is_wp_error( $can ) ) {
		return $can;
	}
	if ( '' !== $child_of ) {
		if ( $tag !== $child_of ) {
			return wpu_bt_err( $tag . ' cannot go inside this module; it takes ' . $child_of . ' items.' );
		}
	} elseif ( 'child' === $info['kind'] ) {
		return wpu_bt_err( $tag . ' is an item of another module and cannot stand alone.' );
	} elseif ( $fullwidth_section !== $info['fullwidth'] ) {
		return wpu_bt_err( $fullwidth_section ? $tag . ' cannot go in a fullwidth section; use a fullwidth module (et_pb_fullwidth_...).' : $tag . ' is a fullwidth module: put it in a section with "fullwidth": true.' );
	}
	$attrs = wpu_bt_divi_attrs( $tag, isset( $in['attrs'] ) ? $in['attrs'] : array(), $warnings );
	if ( is_wp_error( $attrs ) ) {
		return $attrs;
	}
	$node = array( 'tag' => $tag, 'attrs' => $attrs, 'children' => array(), 'content' => '' );
	if ( '' !== $info['child'] ) {
		foreach ( isset( $in['children'] ) ? (array) $in['children'] : array() as $c ) {
			$cn = wpu_bt_divi_module_node( $c, $fullwidth_section, $warnings, $info['child'] );
			if ( is_wp_error( $cn ) ) {
				return $cn;
			}
			$node['children'][] = $cn;
		}
		if ( ! $node['children'] && ! in_array( $tag, array( 'et_pb_signup', 'et_pb_map', 'et_pb_fullwidth_map' ), true ) ) {
			$warnings[] = $tag . ' has no items yet (it takes ' . $info['child'] . ' children).';
		}
		if ( count( $node['children'] ) > 60 ) {
			return wpu_bt_err( 'At most 60 items in one ' . $tag . '.' );
		}
	} elseif ( ! empty( $in['children'] ) ) {
		return wpu_bt_err( $tag . ' does not take child items.' );
	}
	if ( isset( $in['content'] ) && '' === $info['child'] ) {
		$c = wpu_bt_divi_content( $in['content'], $tag );
		if ( is_wp_error( $c ) ) {
			return $c;
		}
		$node['content'] = $c;
	}
	return $node;
}

function wpu_bt_divi_row_node( $in, &$warnings ) {
	$ok = wpu_bt_divi_keys( $in, array( 'columns', 'cols', 'attrs' ), 'row' );
	if ( is_wp_error( $ok ) ) {
		return $ok;
	}
	$in     = (array) $in;
	$struct = wpu_bt_divi_structure( isset( $in['columns'] ) ? $in['columns'] : '4_4' );
	if ( is_wp_error( $struct ) ) {
		return $struct;
	}
	$cols = isset( $in['cols'] ) ? array_values( (array) $in['cols'] ) : array();
	if ( count( $cols ) > count( $struct ) ) {
		return wpu_bt_err( 'This row has ' . count( $struct ) . ' columns ("' . implode( ',', $struct ) . '") but ' . count( $cols ) . ' were sent.' );
	}
	$attrs = wpu_bt_divi_attrs( 'et_pb_row', isset( $in['attrs'] ) ? $in['attrs'] : array(), $warnings );
	if ( is_wp_error( $attrs ) ) {
		return $attrs;
	}
	if ( array( '4_4' ) !== $struct ) {
		$attrs['column_structure'] = implode( ',', $struct );
	}
	$row = array( 'tag' => 'et_pb_row', 'attrs' => $attrs, 'children' => array(), 'content' => '' );
	foreach ( $struct as $i => $width ) {
		$c  = isset( $cols[ $i ] ) ? $cols[ $i ] : array();
		$ok = wpu_bt_divi_keys( $c, array( 'attrs', 'modules' ), 'column' );
		if ( is_wp_error( $ok ) ) {
			return $ok;
		}
		$c = (array) $c;
		$cattr = wpu_bt_divi_attrs( 'et_pb_column', isset( $c['attrs'] ) ? $c['attrs'] : array(), $warnings );
		if ( is_wp_error( $cattr ) ) {
			return $cattr;
		}
		$cattr['type'] = $width;
		$col           = array( 'tag' => 'et_pb_column', 'attrs' => $cattr, 'children' => array(), 'content' => '' );
		foreach ( isset( $c['modules'] ) ? (array) $c['modules'] : array() as $m ) {
			$mn = wpu_bt_divi_module_node( $m, false, $warnings );
			if ( is_wp_error( $mn ) ) {
				return $mn;
			}
			$col['children'][] = $mn;
		}
		$row['children'][] = $col;
	}
	return $row;
}

function wpu_bt_divi_section_node( $in, &$warnings ) {
	$ok = wpu_bt_divi_keys( $in, array( 'fullwidth', 'attrs', 'rows', 'modules' ), 'section' );
	if ( is_wp_error( $ok ) ) {
		return $ok;
	}
	$in    = (array) $in;
	$full  = ! empty( $in['fullwidth'] );
	$attrs = wpu_bt_divi_attrs( 'et_pb_section', isset( $in['attrs'] ) ? $in['attrs'] : array(), $warnings );
	if ( is_wp_error( $attrs ) ) {
		return $attrs;
	}
	unset( $attrs['specialty'] );
	if ( $full ) {
		$attrs['fullwidth'] = 'on';
	} else {
		unset( $attrs['fullwidth'] );
	}
	$sec = array( 'tag' => 'et_pb_section', 'attrs' => $attrs, 'children' => array(), 'content' => '' );
	if ( $full ) {
		foreach ( isset( $in['modules'] ) ? (array) $in['modules'] : array() as $m ) {
			$mn = wpu_bt_divi_module_node( $m, true, $warnings );
			if ( is_wp_error( $mn ) ) {
				return $mn;
			}
			$sec['children'][] = $mn;
		}
		if ( ! empty( $in['rows'] ) ) {
			return wpu_bt_err( 'A fullwidth section takes "modules" (fullwidth modules), not rows.' );
		}
	} else {
		foreach ( isset( $in['rows'] ) ? (array) $in['rows'] : array() as $r ) {
			$rn = wpu_bt_divi_row_node( $r, $warnings );
			if ( is_wp_error( $rn ) ) {
				return $rn;
			}
			$sec['children'][] = $rn;
		}
		if ( ! empty( $in['modules'] ) ) {
			return wpu_bt_err( 'A regular section takes "rows". For fullwidth modules set "fullwidth": true.' );
		}
	}
	return $sec;
}

/** Build a node from input for the place it will sit in (by parent tag). */
function wpu_bt_divi_node_for( $parent, $in, &$warnings ) {
	if ( null === $parent ) {
		return wpu_bt_divi_section_node( $in, $warnings );
	}
	$ptag = $parent['tag'];
	if ( 'et_pb_section' === $ptag ) {
		$full = isset( $parent['attrs']['fullwidth'] ) && 'on' === $parent['attrs']['fullwidth'];
		if ( isset( $parent['attrs']['specialty'] ) && 'on' === $parent['attrs']['specialty'] ) {
			return wpu_bt_err( 'Specialty sections are not edited structurally by the bridge. Change their modules\' content or settings instead.' );
		}
		return $full ? wpu_bt_divi_module_node( $in, true, $warnings ) : wpu_bt_divi_row_node( $in, $warnings );
	}
	if ( 'et_pb_row' === $ptag || 'et_pb_row_inner' === $ptag ) {
		return wpu_bt_err( 'Columns come from the row\'s structure. Replace the row to change its columns, or insert modules into a column.' );
	}
	if ( 'et_pb_column' === $ptag || 'et_pb_column_inner' === $ptag ) {
		return wpu_bt_divi_module_node( $in, false, $warnings );
	}
	$info = wpu_bt_divi_info( $ptag );
	if ( $info && '' !== $info['child'] ) {
		return wpu_bt_divi_module_node( $in, false, $warnings, $info['child'] );
	}
	return wpu_bt_err( $ptag . ' does not take child items.' );
}

function wpu_bt_divi_version_attr() {
	return defined( 'ET_BUILDER_PRODUCT_VERSION' ) ? ET_BUILDER_PRODUCT_VERSION : ( defined( 'ET_BUILDER_VERSION' ) ? ET_BUILDER_VERSION : '4.27' );
}

function wpu_bt_divi_serialize( array $node ) {
	if ( isset( $node['raw_open'] ) ) {
		$open = $node['raw_open'];
	} else {
		$attrs = $node['attrs'];
		if ( 'et_pb_section' === $node['tag'] && empty( $node['parsed'] ) ) {
			$attrs = array( 'fb_built' => '1' ) + $attrs;
		}
		if ( empty( $node['parsed'] ) ) {
			if ( ! isset( $attrs['_builder_version'] ) ) {
				// On Divi 5 the shortcode only exists in memory on its way to Divi's converter: mark it as Divi 4 content.
				$attrs['_builder_version'] = wpu_bt_divi_is_v4() ? wpu_bt_divi_version_attr() : '4.27.4';
			}
			if ( ! isset( $attrs['global_colors_info'] ) ) {
				$attrs['global_colors_info'] = '{}';
			}
		}
		$open = '[' . $node['tag'];
		foreach ( $attrs as $k => $v ) {
			$open .= ' ' . $k . '="' . $v . '"';
		}
		$open .= ']';
	}
	$inner = '';
	foreach ( $node['children'] as $c ) {
		$inner .= wpu_bt_divi_serialize( $c );
	}
	if ( ! $node['children'] ) {
		$inner = $node['content'];
	}
	return $open . $inner . '[/' . $node['tag'] . ']';
}

/* -------------------------------------------------------------------------
 * Page -> tree (for outline and edits)
 * ---------------------------------------------------------------------- */

/** @return array|WP_Error list of top-level nodes */
function wpu_bt_divi_parse( $content ) {
	$content = (string) $content;
	if ( false === strpos( $content, '[et_pb_section' ) || ! preg_match_all( '/\[(\/?)([a-z][a-z0-9_]*)((?:\s[^\]]*)?)\]/', $content, $m, PREG_OFFSET_CAPTURE | PREG_SET_ORDER ) ) {
		return array();
	}
	$root  = array( 'tag' => '', 'children' => array() );
	$stack = array( &$root );
	$pos   = 0;
	foreach ( $m as $t ) {
		$start   = $t[0][1];
		$closing = '/' === $t[1][0];
		$tag     = $t[2][0];
		if ( ! wpu_bt_divi_is_tag( $tag ) ) {
			continue; // an ordinary shortcode inside a module's content
		}
		$top     = &$stack[ count( $stack ) - 1 ];
		$between = substr( $content, $pos, $start - $pos );
		if ( $closing ) {
			if ( $top['tag'] !== $tag ) {
				return wpu_bt_err( 'This page\'s Divi layout is not well formed near "' . substr( $content, max( 0, $start - 30 ), 80 ) . '". Open and save it in Divi first.' );
			}
			if ( ! $top['children'] ) {
				$top['content'] = $between;
			}
			array_pop( $stack );
		} else {
			if ( count( $stack ) > 12 ) {
				return wpu_bt_err( 'This page nests Divi elements too deeply to edit here.' );
			}
			// Read settings ourselves so stored values stay exactly as they are (WordPress's reader unescapes them).
			$attrs = array();
			$plain = '[' . $tag;
			if ( preg_match_all( '/\s+([A-Za-z0-9_]+)="([^"]*)"/', $t[3][0], $am, PREG_SET_ORDER ) ) {
				foreach ( $am as $one ) {
					$attrs[ $one[1] ] = $one[2];
					$plain           .= ' ' . $one[1] . '="' . $one[2] . '"';
				}
			}
			// "plain" = the tag is nothing but name="value" pairs, so it can be rewritten without loss.
			$top['children'][] = array( 'tag' => $tag, 'attrs' => $attrs, 'children' => array(), 'content' => '', 'raw_open' => $t[0][0], 'parsed' => true, 'plain' => preg_replace( '/\s+/', ' ', $t[0][0] ) === preg_replace( '/\s+/', ' ', $plain . ']' ) && count( $attrs ) === count( $am ) );
			$stack[]           = &$top['children'][ count( $top['children'] ) - 1 ];
		}
		$pos = $start + strlen( $t[0][0] );
		unset( $top );
	}
	if ( count( $stack ) !== 1 ) {
		return wpu_bt_err( 'This page\'s Divi layout has an element that is never closed. Open and save it in Divi first.' );
	}
	return $root['children'];
}

function wpu_bt_divi_decode( $v ) {
	return str_replace( array( '%22', '%91', '%93', '%92' ), array( '"', '[', ']', '\\' ), (string) $v );
}

function wpu_bt_divi_outline( array $nodes, $prefix = '', &$out = array() ) {
	foreach ( $nodes as $i => $n ) {
		if ( count( $out ) >= 500 ) {
			break;
		}
		$path = '' === $prefix ? (string) $i : $prefix . '.' . $i;
		$row  = array( 'path' => $path, 'type' => $n['tag'] );
		foreach ( array( 'admin_label', 'column_structure', 'type', 'fullwidth', 'specialty', 'title', 'button_text', 'heading', 'name', 'module_id', 'module_class' ) as $k ) {
			if ( isset( $n['attrs'][ $k ] ) && '' !== $n['attrs'][ $k ] ) {
				$row[ $k ] = substr( wpu_bt_divi_decode( $n['attrs'][ $k ] ), 0, 120 );
			}
		}
		if ( ! $n['children'] && '' !== trim( $n['content'] ) ) {
			$row['text'] = substr( trim( preg_replace( '/\s+/', ' ', wp_strip_all_tags( $n['content'] ) ) ), 0, 140 );
		}
		if ( $n['children'] ) {
			$row['children'] = count( $n['children'] );
		}
		$out[] = $row;
		wpu_bt_divi_outline( $n['children'], $path, $out );
	}
	return $out;
}

/** Reference to the node at $path ("0.1.0.2"), or null. */
function &wpu_bt_divi_ref( array &$nodes, $path ) {
	$null = null;
	$idx  = wpu_bt_parse_path( $path );
	if ( null === $idx || ! $idx ) {
		return $null;
	}
	$list = &$nodes;
	$last = count( $idx ) - 1;
	foreach ( $idx as $d => $i ) {
		if ( ! isset( $list[ $i ] ) ) {
			return $null;
		}
		if ( $d === $last ) {
			return $list[ $i ];
		}
		$list = &$list[ $i ]['children'];
	}
	return $null;
}

/* -------------------------------------------------------------------------
 * Saving
 * ---------------------------------------------------------------------- */

function wpu_bt_divi_meta_keys() {
	return array( '_et_pb_use_builder', '_et_pb_old_content', '_et_builder_version', '_et_pb_built_for_post_type', '_et_pb_page_layout', '_et_pb_side_nav', '_et_pb_show_page_creation' );
}

function wpu_bt_divi_save( $id, $content, $is_new_layout ) {
	kses_remove_filters(); // every new piece was filtered one by one above; untouched pieces are saved as they were
	try {
		$r = wp_update_post( wp_slash( array( 'ID' => $id, 'post_content' => $content ) ), true );
	} finally {
		kses_init(); // always back to the normal rule for this user, even if a plugin's save hook fails
	}
	if ( is_wp_error( $r ) ) {
		return $r;
	}
	update_post_meta( $id, '_et_pb_use_builder', 'on' );
	if ( $is_new_layout ) {
		$product = defined( 'ET_BUILDER_PLUGIN_ACTIVE' ) ? 'Divi Builder' : wp_get_theme( get_template() )->get( 'Name' );
		update_post_meta( $id, '_et_builder_version', 'VB|' . $product . '|' . wpu_bt_divi_version_attr() );
		update_post_meta( $id, '_et_pb_built_for_post_type', get_post_type( $id ) );
		if ( ! metadata_exists( 'post', $id, '_et_pb_old_content' ) ) {
			update_post_meta( $id, '_et_pb_old_content', '' );
		}
		if ( ! defined( 'ET_BUILDER_PLUGIN_ACTIVE' ) && ! metadata_exists( 'post', $id, '_et_pb_page_layout' ) ) {
			update_post_meta( $id, '_et_pb_page_layout', 'et_no_sidebar' );
		}
	}
	if ( class_exists( 'ET_Core_PageResource' ) && method_exists( 'ET_Core_PageResource', 'remove_static_resources' ) ) {
		ET_Core_PageResource::remove_static_resources( $id, 'all' );
	}
	clean_post_cache( $id );
	do_action( 'litespeed_purge_post', $id );
	if ( function_exists( 'rocket_clean_post' ) ) {
		rocket_clean_post( $id );
	}
	return true;
}

/** Undo record: content plus the Divi meta as it was. */
function wpu_bt_divi_undo_items( $id ) {
	$p     = get_post( $id );
	$items = array( array( 'kind' => 'post', 'id' => $id, 'fields' => array( 'post_content' => $p->post_content ) ) );
	$meta  = array();
	foreach ( wpu_bt_divi_meta_keys() as $k ) {
		$meta[ $k ] = metadata_exists( 'post', $id, $k ) ? get_post_meta( $id, $k, true ) : null;
	}
	$items[] = array( 'kind' => 'meta', 'id' => $id, 'values' => $meta );
	return $items;
}

/** The post a Divi tool may work on, or the reason it may not. @return WP_Post|WP_Error */
function wpu_bt_divi_post( $id, $for_write ) {
	$p = get_post( $id );
	if ( ! $p || ! current_user_can( 'edit_post', $id ) || 'revision' === $p->post_type || 0 === strpos( $p->post_type, 'et_' ) || ! wpu_bt_editable_type( $p->post_type ) ) {
		return wpu_bt_err( 'No page or post ' . (int) $id . ' that these tools can work on. (Divi library items, Theme Builder templates and products are edited in Divi.)' );
	}
	if ( $for_write ) {
		if ( ! function_exists( 'wp_check_post_lock' ) ) {
			require_once ABSPATH . 'wp-admin/includes/post.php';
		}
		$locker = wp_check_post_lock( $id );
		if ( $locker ) {
			$u = get_userdata( $locker );
			return wpu_bt_err( ( $u ? $u->display_name : 'Someone' ) . ' has this page open for editing right now. Try again when they have finished.' );
		}
	}
	return $p;
}

function wpu_bt_divi_ready() {
	if ( ! wpu_bt_has_divi() ) {
		return wpu_bt_err( 'Divi is not active on this site.' );
	}
	if ( ! wpu_bt_divi_is_v4() && '' === wpu_bt_divi5_converter() ) {
		return wpu_bt_err( 'This version of Divi 5 has no layout converter, so layouts cannot be built here. Update Divi. builder_page_text and builder_replace_text still work for text.' );
	}
	$boot = wpu_bt_divi_boot();
	return '' === $boot ? true : wpu_bt_err( $boot );
}

function wpu_bt_divi_avail() {
	return wpu_bt_has_divi() && ( wpu_bt_divi_is_v4() || '' !== wpu_bt_divi5_converter() );
}

/* -------------------------------------------------------------------------
 * Tools
 * ---------------------------------------------------------------------- */

wpu_bt_define_tool( 'divi_modules', array(
	'title'       => 'Divi modules',
	'description' => 'Divi modules available on this site (including ones added by other plugins): type, name, whether it is fullwidth, and the child item it takes. Pass names to get a module\'s settings: content settings with their options, and (design true) every design setting name.',
	'cap'         => 'edit_posts',
	'available'   => 'wpu_bt_divi_avail',
	'props'       => array(
		'names'  => array( 'type' => 'array', 'items' => array( 'type' => 'string' ), 'description' => 'Up to 8 module types, e.g. ["blurb","accordion"].' ),
		'design' => array( 'type' => 'boolean', 'description' => 'With names: also list design and advanced setting names.' ),
	),
	'run'         => function ( $a ) {
		$ok = wpu_bt_divi_ready();
		if ( is_wp_error( $ok ) ) {
			return $ok;
		}
		$names = isset( $a['names'] ) ? array_slice( array_filter( array_map( 'wpu_bt_divi_tag', (array) $a['names'] ) ), 0, 8 ) : array();
		if ( $names ) {
			$out = array();
			foreach ( $names as $tag ) {
				$info = wpu_bt_divi_info( $tag );
				if ( ! $info ) {
					$out[] = array( 'type' => $tag, 'error' => 'unknown module' );
					continue;
				}
				$m       = wpu_bt_divi_module( $tag );
				$content = array();
				foreach ( $m ? (array) $m->get_fields() : array() as $k => $f ) {
					if ( '_' === $k[0] || ( isset( $f['type'] ) && in_array( $f['type'], array( 'skip', 'computed', 'hidden' ), true ) ) ) {
						continue;
					}
					$row = array( 'type' => isset( $f['type'] ) ? $f['type'] : '' );
					if ( ! empty( $f['label'] ) && is_string( $f['label'] ) ) {
						$row['label'] = $f['label'];
					}
					if ( ! empty( $f['options'] ) && is_array( $f['options'] ) && count( $f['options'] ) <= 40 ) {
						$row['options'] = array_keys( $f['options'] );
					}
					if ( isset( $f['default'] ) && is_scalar( $f['default'] ) ) {
						$row['default'] = $f['default'];
					}
					$content[ $k ] = $row;
				}
				$row = array( 'type' => $tag, 'name' => $info['name'], 'kind' => $info['kind'], 'fullwidth' => $info['fullwidth'], 'child' => $info['child'], 'refused' => is_wp_error( wpu_bt_divi_writable( $tag ) ), 'settings' => $content ? $content : new stdClass(), 'takes_content' => isset( $content['content'] ) || isset( $content['raw_content'] ) );
				if ( wpu_bt_bool( $a, 'design' ) ) {
					$row['design_settings'] = array_values( preg_grep( '/(_tablet|_phone|_last_edited|__hover|__hover_enabled|__sticky|__sticky_enabled)$/', array_diff( array_keys( wpu_bt_divi_fields( $tag ) ), array_keys( $content ) ), PREG_GREP_INVERT ) );
					$row['design_settings'][] = 'border_radii, border_width_all, border_color_all, border_style_all (and _top/_right/_bottom/_left), box_shadow_style, box_shadow_color ...';
				}
				$out[] = $row;
			}
			return array( 'modules' => $out, 'note' => 'Every setting also has _tablet and _phone variants, and many have __hover. Values are text: "on"/"off" for switches, "20px|20px|20px|20px" for spacing (top|right|bottom|left).' );
		}
		wpu_bt_divi_load( null );
		$out = array();
		foreach ( array( 'get_parent_modules', 'get_child_modules' ) as $fn ) {
			foreach ( (array) ET_Builder_Element::$fn( 'page' ) as $tag => $m ) {
				$info  = wpu_bt_divi_info( $tag );
				$out[] = array( 'type' => $tag, 'name' => $info['name'], 'kind' => $info['kind'], 'fullwidth' => $info['fullwidth'], 'child' => $info['child'], 'refused' => is_wp_error( wpu_bt_divi_writable( $tag ) ) );
			}
		}
		return array(
			'divi_version' => wpu_bt_divi_version_attr(),
			'count'        => count( $out ),
			'modules'      => $out,
			'structure'    => 'section > row (columns "1_2,1_2") > column > module > child items. Fullwidth sections hold fullwidth modules directly.',
			'columns'      => array( '4_4', '1_2,1_2', '1_3,1_3,1_3', '1_4,1_4,1_4,1_4', '2_3,1_3', '1_3,2_3', '1_4,3_4', '3_4,1_4', '1_2,1_4,1_4', '1_4,1_4,1_2', '1_4,1_2,1_4', '1_5,1_5,1_5,1_5,1_5', '1_6,1_6,1_6,1_6,1_6,1_6', '2_5,3_5', '3_5,2_5' ),
		);
	},
) );

wpu_bt_define_tool( 'divi_page_get', array(
	'title'       => 'Divi page outline',
	'description' => 'The structure of a Divi page: every section, row, column, module and item with its path (for divi_page_edit), type, label and a text preview. Pass path to get one element\'s full settings and content.',
	'cap'         => 'edit_posts',
	'available'   => 'wpu_bt_divi_avail',
	'props'       => array(
		'id'   => array( 'type' => 'integer' ),
		'path' => array( 'type' => 'string', 'description' => 'e.g. "0.1.0.2" for one element in full.' ),
	),
	'required'    => array( 'id' ),
	'run'         => function ( $a ) {
		$id = absint( $a['id'] );
		$p  = wpu_bt_divi_post( $id, false );
		if ( is_wp_error( $p ) ) {
			return $p;
		}
		if ( wpu_bt_divi5_is_content( $p->post_content ) ) {
			$doc = wpu_bt_divi5_parse( $p->post_content );
			if ( is_wp_error( $doc ) ) {
				return $doc;
			}
			if ( isset( $a['path'] ) && '' !== $a['path'] ) {
				$n = wpu_bt_divi5_ref( $doc['nodes'], (string) $a['path'] );
				if ( null === $n ) {
					return wpu_bt_err( 'No element at path ' . sanitize_text_field( (string) $a['path'] ) . '.' );
				}
				return array( 'path' => (string) $a['path'], 'divi' => 5, 'type' => $n['tag'], 'divi4_name' => wpu_bt_divi5_d4_tag( $n['tag'] ), 'settings' => wpu_bt_divi5_attrs( $n ), 'children' => count( $n['children'] ), 'note' => 'These are Divi 5\'s stored settings. To change them, use divi_page_edit with the Divi 4 setting names from divi_modules; they are converted for you.' );
			}
			return array( 'id' => $id, 'title' => $p->post_title, 'status' => $p->post_status, 'url' => get_permalink( $id ), 'divi' => 5, 'elements' => wpu_bt_divi5_outline( $doc['nodes'] ) );
		}
		$tree = wpu_bt_divi_parse( $p->post_content );
		if ( is_wp_error( $tree ) ) {
			return $tree;
		}
		if ( ! $tree ) {
			return array( 'id' => $id, 'title' => $p->post_title, 'divi' => false, 'note' => 'This page has no Divi layout. divi_page_build can create one.' );
		}
		if ( isset( $a['path'] ) && '' !== $a['path'] ) {
			$n = wpu_bt_divi_ref( $tree, (string) $a['path'] );
			if ( null === $n ) {
				return wpu_bt_err( 'No element at path ' . sanitize_text_field( (string) $a['path'] ) . '.' );
			}
			return array( 'path' => (string) $a['path'], 'type' => $n['tag'], 'attrs' => array_map( 'wpu_bt_divi_decode', $n['attrs'] ), 'content' => $n['children'] ? null : wpu_bt_trim( $n['content'], 20000 ), 'children' => count( $n['children'] ) );
		}
		return array( 'id' => $id, 'title' => $p->post_title, 'status' => $p->post_status, 'url' => get_permalink( $id ), 'divi' => true, 'elements' => wpu_bt_divi_outline( $tree ) );
	},
) );

wpu_bt_define_tool( 'divi_page_build', array(
	'title'       => 'Build a Divi page',
	'description' => 'Create a new Divi page (draft) or set the layout of an existing page from a typed layout: '
		. '{"sections":[{"attrs":{"background_color":"#f5f5f5"},"rows":[{"columns":"1_2,1_2","cols":[{"modules":[{"type":"text","content":"<h2>Title</h2><p>Text</p>"},{"type":"button","attrs":{"button_text":"Call us","button_url":"https://..."}}]},{"modules":[{"type":"image","attrs":{"src":"https://...","alt":"..."}}]}]}]},{"fullwidth":true,"modules":[{"type":"fullwidth_header","attrs":{"title":"..."}}]}]}. '
		. 'Modules with items take "children" (accordion > accordion_item, tabs > tab, slider > slide, pricing_tables > pricing_table, contact_form > contact_field, counters > counter, social_media_follow > social_media_follow_network). '
		. 'Everything is checked against Divi on this site: unknown modules and misplaced items are refused, unknown settings are dropped with a warning, the Code module is refused. mode "replace" (default) or "append" for an existing page. dry_run returns the checks without saving. Returns a preview link and a change_id.',
	'cap'         => 'edit_pages',
	'available'   => 'wpu_bt_divi_avail',
	'props'       => array(
		'id'        => array( 'type' => 'integer', 'description' => 'Existing page or post. Omit to create a new one.' ),
		'title'     => array( 'type' => 'string', 'description' => 'For a new page.' ),
		'post_type' => array( 'type' => 'string', 'description' => 'For a new one: page (default) or post.' ),
		'layout'    => array( 'type' => 'object' ),
		'mode'      => array( 'type' => 'string', 'enum' => array( 'replace', 'append' ) ),
		'dry_run'   => array( 'type' => 'boolean' ),
	),
	'required'    => array( 'layout' ),
	'write'       => true,
	'run'         => function ( $a ) {
		$ok = wpu_bt_divi_ready();
		if ( is_wp_error( $ok ) ) {
			return $ok;
		}
		$layout   = (array) $a['layout'];
		$sections = isset( $layout['sections'] ) ? array_values( (array) $layout['sections'] ) : array();
		if ( ! $sections || count( $sections ) > 60 ) {
			return wpu_bt_err( 'layout needs 1 to 60 sections.' );
		}
		$warnings = array();
		$shortcode = '';
		$count     = 0;
		foreach ( $sections as $i => $s ) {
			$node = wpu_bt_divi_section_node( $s, $warnings );
			if ( is_wp_error( $node ) ) {
				return wpu_bt_err( 'Section ' . $i . ': ' . $node->get_error_message() );
			}
			$shortcode .= wpu_bt_divi_serialize( $node );
			$count     += 1;
		}
		if ( strlen( $shortcode ) > 2 * MB_IN_BYTES ) {
			return wpu_bt_err( 'The layout is larger than 2 MB.' );
		}
		$warnings = array_values( array_unique( $warnings ) );
		$v5       = wpu_bt_divi_is_v5();
		if ( $v5 ) {
			// Divi 5: hand the checked layout to Divi's own converter; only its Divi 5 blocks are saved.
			$shortcode = wpu_bt_divi5_convert( $shortcode );
			if ( is_wp_error( $shortcode ) ) {
				return $shortcode;
			}
		}
		if ( wpu_bt_bool( $a, 'dry_run' ) ) {
			if ( $v5 ) {
				$doc = wpu_bt_divi5_parse( $shortcode );
				return is_wp_error( $doc ) ? $doc : array( 'dry_run' => true, 'divi' => 5, 'sections' => $count, 'warnings' => $warnings, 'elements' => wpu_bt_divi5_outline( $doc['nodes'] ) );
			}
			return array( 'dry_run' => true, 'sections' => $count, 'warnings' => $warnings, 'elements' => wpu_bt_divi_outline( wpu_bt_divi_parse( $shortcode ) ) );
		}
		$mode = isset( $a['mode'] ) ? (string) $a['mode'] : 'replace';
		if ( ! empty( $a['id'] ) ) {
			$id = absint( $a['id'] );
			$p  = wpu_bt_divi_post( $id, true );
			if ( is_wp_error( $p ) ) {
				return $p;
			}
			$builder = wpu_bt_post_builder( $id );
			if ( in_array( $builder, array( 'elementor', 'bricks', 'beaver_builder', 'breakdance', 'seedprod' ), true ) ) {
				return wpu_bt_err( 'This page is built with ' . $builder . '. Create a new page for a Divi layout.' );
			}
			if ( 'append' === $mode && ! in_array( $builder, array( 'divi', 'empty' ), true ) ) {
				return wpu_bt_err( 'This page is not a Divi page, so there is no Divi layout to append to. Use mode "replace" (its current content is kept for undo).' );
			}
			$is5 = wpu_bt_divi5_is_content( $p->post_content );
			if ( $is5 && ! $v5 ) {
				return wpu_bt_err( 'This page is in Divi 5 form but the site runs Divi 4, so it is not changed here.' );
			}
			if ( $v5 && 'append' === $mode && 'divi' === $builder && ! $is5 ) {
				return wpu_bt_err( 'This page is still in Divi 4 form. Open and save it in Divi 5 once so Divi converts it, or use mode "replace".' );
			}
			$undo = wpu_bt_divi_undo_items( $id );
			if ( $v5 ) {
				if ( 'append' === $mode && $is5 ) {
					$doc = wpu_bt_divi5_parse( $p->post_content );
					if ( is_wp_error( $doc ) ) {
						return $doc;
					}
					$add = wpu_bt_divi5_parse( $shortcode );
					if ( is_wp_error( $add ) ) {
						return $add;
					}
					if ( wpu_bt_divi5_serialize( $doc ) !== trim( $p->post_content ) ) {
						return wpu_bt_err( 'This page\'s Divi layout is stored in a form that cannot be rewritten exactly, so nothing is appended here. Open and save it in Divi first.' );
					}
					$doc['nodes'] = array_merge( $doc['nodes'], $add['nodes'] );
					$new          = wpu_bt_divi5_serialize( $doc );
					if ( strlen( $new ) > 2 * MB_IN_BYTES || wpu_bt_divi5_count( $doc['nodes'] ) > 4000 ) {
						return wpu_bt_err( 'The page would be larger than 2 MB or 4000 elements.' );
					}
				} else {
					$new = wpu_bt_divi5_wrap( $shortcode );
				}
			} else {
				$new = 'append' === $mode && 'divi' === $builder ? $p->post_content . $shortcode : $shortcode;
			}
			$r    = wpu_bt_divi_save( $id, $new, 'divi' !== $builder );
			if ( is_wp_error( $r ) ) {
				return $r;
			}
			$cid = wpu_bt_change_add( 'divi_page_build', ( 'append' === $mode ? 'Added ' : 'Set ' ) . $count . ' Divi sections on #' . $id . ' "' . get_the_title( $id ) . '"', array( 'kind' => 'multi', 'items' => $undo ) );
		} else {
			$type = isset( $a['post_type'] ) ? sanitize_key( $a['post_type'] ) : 'page';
			if ( ! wpu_bt_editable_type( $type ) ) {
				return wpu_bt_err( 'Unsupported post type: ' . $type );
			}
			$pto = get_post_type_object( $type );
			if ( ! current_user_can( $pto->cap->create_posts ) ) {
				return wpu_bt_err( 'You cannot create ' . $pto->label . '.' );
			}
			$title = sanitize_text_field( wpu_bt_str( $a, 'title' ) );
			if ( '' === $title ) {
				return wpu_bt_err( 'A new page needs a title.' );
			}
			$id = wp_insert_post( wp_slash( array( 'post_type' => $type, 'post_status' => 'draft', 'post_title' => $title ) ), true );
			if ( is_wp_error( $id ) ) {
				return $id;
			}
			$r = wpu_bt_divi_save( $id, $v5 ? wpu_bt_divi5_wrap( $shortcode ) : $shortcode, true );
			if ( is_wp_error( $r ) ) {
				wp_delete_post( $id, true ); // do not leave an empty draft behind
				return $r;
			}
			$cid = wpu_bt_change_add( 'divi_page_build', 'Created Divi ' . $type . ' #' . $id . ' "' . $title . '" (' . $count . ' sections)', array( 'kind' => 'trash', 'id' => $id ) );
		}
		return array(
			'id'        => $id,
			'status'    => get_post_status( $id ),
			'sections'  => $count,
			'warnings'  => $warnings,
			'url'       => get_permalink( $id ),
			'preview'   => get_preview_post_link( $id ),
			'edit_in_divi' => add_query_arg( 'et_fb', '1', get_permalink( $id ) ),
			'change_id' => $cid,
		);
	},
) );

wpu_bt_define_tool( 'divi_page_edit', array(
	'title'       => 'Edit a Divi page',
	'description' => 'Targeted changes to a Divi page by path (from divi_page_get). Operations run in order: '
		. '{"op":"set_attrs","path":"0.0.1.0","attrs":{"button_text":"Book now","background_color":null}} (null removes a setting); '
		. '{"op":"set_content","path":"0.0.0.0","content":"<p>New text</p>"}; '
		. '{"op":"insert","parent":"0.0.1","index":0,"node":{...}} - parent "" adds a section, a section path adds a row, a column path adds a module, a module path adds a child item; node is the same shape as in divi_page_build; '
		. '{"op":"replace","path":"1","node":{...}}; {"op":"remove","path":"2.0"}; {"op":"duplicate","path":"1"}; {"op":"move","path":"3","index":0} (within the same parent). '
		. 'Paths are read fresh for each operation, so later paths must allow for earlier inserts and removals. Elements you do not touch stay exactly as Divi saved them. dry_run shows the resulting outline. Returns a change_id.',
	'cap'         => 'edit_posts',
	'available'   => 'wpu_bt_divi_avail',
	'props'       => array(
		'id'         => array( 'type' => 'integer' ),
		'operations' => array( 'type' => 'array', 'items' => array( 'type' => 'object' ), 'description' => 'Up to 40.' ),
		'dry_run'    => array( 'type' => 'boolean' ),
	),
	'required'    => array( 'id', 'operations' ),
	'write'       => true,
	'run'         => function ( $a ) {
		$ok = wpu_bt_divi_ready();
		if ( is_wp_error( $ok ) ) {
			return $ok;
		}
		$id = absint( $a['id'] );
		$p  = wpu_bt_divi_post( $id, ! wpu_bt_bool( $a, 'dry_run' ) );
		if ( is_wp_error( $p ) ) {
			return $p;
		}
		if ( 'divi' !== wpu_bt_post_builder( $id ) ) {
			return wpu_bt_err( 'This is not a Divi page. Use divi_page_build to give it a Divi layout.' );
		}
		if ( wpu_bt_divi5_is_content( $p->post_content ) ) {
			if ( ! wpu_bt_divi_is_v5() ) {
				return wpu_bt_err( 'This page is in Divi 5 form but the site runs Divi 4, so it is not changed here.' );
			}
			return wpu_bt_divi5_edit( $p, $a );
		}
		if ( wpu_bt_divi_is_v5() ) {
			return wpu_bt_err( 'This page is still in Divi 4 form. Open and save it in Divi 5 once so Divi converts it; then it can be edited here. builder_replace_text works for text meanwhile.' );
		}
		$tree = wpu_bt_divi_parse( $p->post_content );
		if ( is_wp_error( $tree ) ) {
			return $tree;
		}
		// Anything outside Divi's shortcodes (rare) would be lost on re-serialising: refuse instead.
		$check = '';
		foreach ( $tree as $n ) {
			$check .= wpu_bt_divi_serialize( $n );
		}
		if ( $check !== preg_replace( '/\]\s+\[(\/?et_pb_)/', '][$1', trim( $p->post_content ) ) ) {
			return wpu_bt_err( 'This page has content outside Divi\'s layout (or unusual formatting), so it cannot be edited structurally without risk. Use builder_replace_text for text, or open and save it in Divi first.' );
		}
		$ops = (array) $a['operations'];
		if ( ! $ops || count( $ops ) > 40 ) {
			return wpu_bt_err( 'Send 1 to 40 operations.' );
		}
		$warnings = array();
		$log      = array();
		$bytes    = strlen( $p->post_content ); // running upper bound, so a chain of copies stops early
		foreach ( $ops as $n => $op ) {
			$op   = (array) $op;
			$kind = isset( $op['op'] ) ? (string) $op['op'] : '';
			$fail = function ( $msg ) use ( $n ) {
				return wpu_bt_err( 'Operation ' . $n . ': ' . $msg );
			};
			if ( 'insert' === $kind ) {
				$ppath  = isset( $op['parent'] ) ? (string) $op['parent'] : '';
				$parent = null;
				if ( '' !== $ppath ) {
					$parent = &wpu_bt_divi_ref( $tree, $ppath );
					if ( null === $parent ) {
						return $fail( 'no element at parent path ' . sanitize_text_field( $ppath ) . '.' );
					}
				}
				$node = wpu_bt_divi_node_for( $parent, isset( $op['node'] ) ? $op['node'] : array(), $warnings );
				if ( is_wp_error( $node ) ) {
					return $fail( $node->get_error_message() );
				}
				if ( null === $parent ) {
					$list = &$tree;
				} else {
					if ( ! $parent['children'] && '' !== trim( $parent['content'] ) ) {
						return $fail( 'the element at ' . sanitize_text_field( $ppath ) . ' holds content the bridge cannot place items next to. Change it in Divi.' );
					}
					$list              = &$parent['children'];
					$parent['content'] = '';
				}
				$at = isset( $op['index'] ) ? max( 0, min( count( $list ), (int) $op['index'] ) ) : count( $list );
				array_splice( $list, $at, 0, array( $node ) );
				$log[] = array( 'op' => $n, 'inserted' => $node['tag'], 'at' => ( '' === $ppath ? '' : $ppath . '.' ) . $at );
				unset( $list, $parent );
				continue;
			}
			$path = isset( $op['path'] ) ? (string) $op['path'] : '';
			$node = &wpu_bt_divi_ref( $tree, $path );
			if ( null === $node ) {
				return $fail( 'no element at path ' . sanitize_text_field( $path ) . '.' );
			}
			$cut   = strrpos( $path, '.' );
			$ppath = false === $cut ? '' : substr( $path, 0, $cut );
			$idx   = (int) ( false === $cut ? $path : substr( $path, $cut + 1 ) );
			if ( 'set_attrs' === $kind ) {
				$tag = $node['tag'];
				$can = wpu_bt_divi_writable( $tag );
				if ( is_wp_error( $can ) ) {
					return $fail( $can->get_error_message() );
				}
				if ( isset( $node['attrs']['_dynamic_attributes'] ) ) {
					return $fail( 'this element uses Divi dynamic content, so it is changed in Divi.' );
				}
				if ( empty( $node['plain'] ) && isset( $node['parsed'] ) ) {
					return $fail( 'this element has settings stored in a form that cannot be rewritten safely. Change it in Divi.' );
				}
				foreach ( isset( $op['attrs'] ) ? (array) $op['attrs'] : array() as $k => $v ) {
					$k = (string) $k;
					if ( in_array( $k, array( 'type', 'column_structure', 'fullwidth', 'specialty', 'fb_built', 'global_module', 'global_parent' ), true ) ) {
						return $fail( 'setting "' . $k . '" is structural; replace the element instead.' );
					}
					if ( null === $v ) {
						if ( '_' !== substr( $k, 0, 1 ) && ! in_array( $k, array( 'global_colors_info', 'saved_tabs', 'template_type', 'ab_subject', 'ab_subject_id', 'ab_goal', 'theme_builder_area' ), true ) ) {
							unset( $node['attrs'][ $k ] );
						}
						continue;
					}
					$one = wpu_bt_divi_attrs( $tag, array( $k => $v ), $warnings );
					if ( is_wp_error( $one ) ) {
						return $fail( $one->get_error_message() );
					}
					$node['attrs'] = array_merge( $node['attrs'], $one );
				}
				unset( $node['raw_open'] ); // other stored values are written back unchanged
				$log[] = array( 'op' => $n, 'set_attrs' => $path );
			} elseif ( 'set_content' === $kind ) {
				$info = wpu_bt_divi_info( $node['tag'] );
				if ( ! $info || 'structure' === $info['kind'] || '' !== $info['child'] || $node['children'] ) {
					return $fail( $node['tag'] . ' holds other elements, not content.' );
				}
				$can = wpu_bt_divi_writable( $node['tag'] );
				if ( is_wp_error( $can ) ) {
					return $fail( $can->get_error_message() );
				}
				if ( isset( $node['attrs']['_dynamic_attributes'] ) ) {
					return $fail( 'this element uses Divi dynamic content, so it is changed in Divi.' );
				}
				$c = wpu_bt_divi_content( isset( $op['content'] ) ? $op['content'] : '', $node['tag'] );
				if ( is_wp_error( $c ) ) {
					return $fail( $c->get_error_message() );
				}
				$node['content'] = $c;
				$log[]           = array( 'op' => $n, 'set_content' => $path );
			} elseif ( in_array( $kind, array( 'remove', 'duplicate', 'move', 'replace' ), true ) ) {
				unset( $node );
				$par = null;
				if ( '' === $ppath ) {
					$list = &$tree;
				} else {
					$par = &wpu_bt_divi_ref( $tree, $ppath );
					if ( in_array( $par['tag'], array( 'et_pb_row', 'et_pb_row_inner' ), true ) ) {
						return $fail( 'columns cannot be removed, moved or duplicated one by one. Replace the row to change its columns.' );
					}
					if ( isset( $par['attrs']['specialty'] ) && 'on' === $par['attrs']['specialty'] ) {
						return $fail( 'the columns of a specialty section are changed in Divi.' );
					}
					$list = &$par['children'];
				}
				if ( 'duplicate' === $kind ) {
					$bytes += strlen( wpu_bt_divi_serialize( $list[ $idx ] ) );
					if ( $bytes > 2 * MB_IN_BYTES ) {
						return $fail( 'the page would be larger than 2 MB.' );
					}
				}
				if ( 'duplicate' === $kind && wpu_bt_divi_tree_refused( $list[ $idx ] ) ) {
					return $fail( 'this element holds a module the bridge does not write (a Code module or one from another plugin), so it is not copied.' );
				}
				if ( 'remove' === $kind ) {
					array_splice( $list, $idx, 1 );
				} elseif ( 'duplicate' === $kind ) {
					array_splice( $list, $idx + 1, 0, array( $list[ $idx ] ) );
				} elseif ( 'move' === $kind ) {
					$to   = isset( $op['index'] ) ? max( 0, min( count( $list ) - 1, (int) $op['index'] ) ) : 0;
					$item = array_splice( $list, $idx, 1 );
					array_splice( $list, $to, 0, $item );
				} else {
					$new = wpu_bt_divi_node_for( $par, isset( $op['node'] ) ? $op['node'] : array(), $warnings );
					if ( is_wp_error( $new ) ) {
						return $fail( $new->get_error_message() );
					}
					$list[ $idx ] = $new;
				}
				$log[] = array( 'op' => $n, $kind => $path );
				unset( $list, $par );
				if ( 'duplicate' === $kind && wpu_bt_divi_count( $tree ) > 4000 ) {
					return $fail( 'the page would have more than 4000 elements.' );
				}
			} else {
				return $fail( 'unknown op "' . sanitize_text_field( $kind ) . '". Use set_attrs, set_content, insert, replace, remove, duplicate or move.' );
			}
			unset( $node );
		}
		$new = '';
		foreach ( $tree as $n ) {
			$new .= wpu_bt_divi_serialize( $n );
		}
		if ( strlen( $new ) > 2 * MB_IN_BYTES || wpu_bt_divi_count( $tree ) > 4000 ) {
			return wpu_bt_err( 'The page would be larger than 2 MB or 4000 elements.' );
		}
		$warnings = array_values( array_unique( $warnings ) );
		if ( wpu_bt_bool( $a, 'dry_run' ) ) {
			return array( 'dry_run' => true, 'operations' => $log, 'warnings' => $warnings, 'elements' => wpu_bt_divi_outline( $tree ) );
		}
		if ( $new === $p->post_content ) {
			return array( 'id' => $id, 'changed' => false, 'operations' => $log );
		}
		$undo = wpu_bt_divi_undo_items( $id );
		$r    = wpu_bt_divi_save( $id, $new, false );
		if ( is_wp_error( $r ) ) {
			return $r;
		}
		$cid = wpu_bt_change_add( 'divi_page_edit', 'Edited Divi layout on #' . $id . ' "' . get_the_title( $id ) . '" (' . count( $log ) . ' operations)', array( 'kind' => 'multi', 'items' => $undo ) );
		return array( 'id' => $id, 'operations' => $log, 'warnings' => $warnings, 'url' => get_permalink( $id ), 'preview' => get_preview_post_link( $id ), 'change_id' => $cid );
	},
) );
