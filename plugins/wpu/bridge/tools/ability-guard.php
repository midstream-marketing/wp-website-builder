<?php
/**
 * Safety layer for the AI actions that page builders ship themselves.
 *
 * Breakdance 3 / Oxygen 6 and SeedProd 6.20+ register page-building actions with the WordPress Abilities API,
 * and the bridge reaches them through abilities_list / ability_run. Those actions were made for a trusted
 * administrator at the keyboard: they do not filter what they are given, and the builders can run PHP and
 * print unescaped markup from ordinary-looking settings. Text on a page can try to steer an AI, so:
 *
 *   1. Changing anything with a builder's actions is OFF until an administrator switches it on
 *      (Tools > WPU Bridge). Only a short list of harmless look-ups works without the switch.
 *   2. Only actions on the bridge's own list run at all; anything a builder adds later is blocked until
 *      the list is updated. Resets, imports, licence keys and site-wide code settings are never run.
 *   3. The input of every action that writes is checked: HTML is parsed (not pattern-matched) for script,
 *      embeds and event handlers; code elements, PHP conditions and queries, dynamic-data shortcodes,
 *      code-named settings and unsafe ids, tags and attribute names are refused.
 *   4. Changes to anything live or site-wide need a one-time code that is tied to the exact request, so the
 *      AI has to come back to the person first.
 *   5. The page is saved before the change, so it gets an Undo. If it cannot be saved, the change is refused.
 *
 * This lowers the risk; it cannot remove it. A builder may read a setting in a way this file does not know.
 * That is why the switch is off by default and says so.
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/** Which builder an ability belongs to: breakdance, oxygen, seedprod, adapter, or ''. */
function wpu_bt_guard_builder( $name ) {
	$ns = strtok( (string) $name, '/' );
	if ( in_array( $ns, array( 'breakdance', 'oxygen', 'seedprod' ), true ) ) {
		return $ns;
	}
	return 'mcp-adapter' === $ns ? 'adapter' : '';
}

/** The bridge's list. Class per action: read (always), look (needs the switch), write, confirm, blocked. */
function wpu_bt_guard_table( $builder ) {
	if ( 'seedprod' === $builder ) {
		return array(
			'get-status'         => array( 'read' ),
			'list-pages'         => array( 'read' ),
			'get-page'           => array( 'read' ),
			'get-global-css'     => array( 'read' ),
			'save-page'          => array( 'write', '', 'id' ),
			'toggle-coming-soon' => array( 'confirm', 'it can hide the whole site from visitors' ),
			'toggle-maintenance' => array( 'confirm', 'it can hide the whole site from visitors' ),
			'toggle-theme'       => array( 'confirm', 'it replaces the whole site\'s theme with SeedProd\'s' ),
			'save-global-css'    => array( 'confirm', 'it replaces the site-wide custom CSS' ),
			'activate-license'   => array( 'blocked', 'licence keys are entered in wp-admin, never through Claude' ),
			'import-theme'       => array( 'blocked', 'it imports a whole theme from a web address' ),
		);
	}
	$read = array( 'get-instructions', 'get-ecommerce-instructions', 'site-info', 'get-global-settings', 'preview-global-settings-css', 'get-post-details', 'search-posts', 'get-template-conditions', 'get-dynamic-fields', 'get-dynamic-data-categories', 'get-maintenance-mode', 'get-css-selectors', 'get-css-variables', 'get-media-sizes', 'get-breakpoints', 'get-element-slugs', 'get-element-schemas', 'get-element-css', 'get-post-tree', 'get-element-conditions', 'search-condition-values', 'get-skill', 'design-system-init', 'get-component-editable-properties' );
	$t    = array_fill_keys( $read, array( 'read' ) );
	// Look-ups that show visitors' data or settings, or that run the page (and whatever is stored in it).
	foreach ( array( 'preview-post', 'preview-element', 'get-post-css-files', 'get-dropdown-options', 'get-form-submissions', 'get-form-submission', 'get-settings', 'get-woocommerce-templates', 'get-woocommerce-template' ) as $a ) {
		$t[ $a ] = array( 'look' );
	}
	foreach ( array( 'edit-post', 'html-to-page', 'set-element-interactions', 'set-element-animations', 'set-element-conditions', 'set-element-variable-overrides', 'set-component-instance-properties', 'set-component-editable-properties' ) as $a ) {
		$t[ $a ] = array( 'write', '', 'post_id' );
	}
	foreach ( array( 'create-post', 'create-reusable-global-block', 'create-reusable-block', 'create-component', 'mark-submission-read' ) as $a ) {
		$t[ $a ] = array( 'write' );
	}
	$confirm = array(
		'set-global-settings'     => 'it changes colours, fonts and defaults on every page',
		'set-maintenance-mode'    => 'it can hide the whole site from visitors',
		'set-home-page'           => 'it changes the site\'s home page',
		'insert-stylesheet'       => 'it adds CSS that applies across the site',
		'delete-css-selectors'    => 'it removes global CSS classes that pages may use',
		'insert-css-variables'    => 'it changes global CSS variables',
		'delete-css-variables'    => 'it removes global CSS variables that pages may use',
		'create-template'         => 'a template, header or footer applies to many pages at once',
		'set-template-conditions' => 'it changes where a template, header or footer applies',
		'create-popup'            => 'a popup can appear on many pages',
		'set-popup-settings'      => 'it changes where and when a popup appears',
		'change-post-status'      => 'it publishes, unpublishes or trashes a page',
		'set-element-form'        => 'it sets where a form sends what visitors enter (email addresses, webhooks)',
	);
	foreach ( $confirm as $a => $why ) {
		$t[ $a ] = array( 'confirm', $why, in_array( $a, array( 'set-template-conditions', 'set-popup-settings', 'change-post-status', 'set-element-form' ), true ) ? 'post_id' : '' );
	}
	$blocked = array(
		'run-site-tool'                      => 'it resets, imports or rewrites the whole builder install with no undo',
		'set-settings'                       => 'it can set site-wide header and footer code and change who may use the builder',
		'set-woocommerce-template'           => 'it writes template files',
		'delete-woocommerce-template'        => 'it deletes template files',
		'list-design-libraries'              => 'design libraries are fetched from other servers',
		'get-design-library-items'           => 'it fetches from a web address the caller chooses',
		'get-design-library-item'            => 'it fetches from a web address the caller chooses',
		'insert-design-library-item'         => 'it inserts a layout from another server that the bridge cannot check',
		'import-design-library-site'         => 'it imports a whole site from another server',
		'import-design-library-dependencies' => 'it imports settings from another server',
		'report-bug'                         => 'bug reports are filed by a person',
	);
	foreach ( $blocked as $a => $why ) {
		$t[ $a ] = array( 'blocked', $why );
	}
	return $t;
}

/**
 * Policy for one ability.
 * @return array{builder:string,class:string,why:string,post_arg:string}
 */
function wpu_bt_guard_policy( $name ) {
	$builder = wpu_bt_guard_builder( $name );
	$p       = array( 'builder' => $builder, 'class' => 'ok', 'why' => '', 'post_arg' => '' );
	if ( '' === $builder ) {
		return $p; // another plugin's ability: passed through as before
	}
	if ( 'adapter' === $builder ) {
		$p['class'] = 'blocked';
		$p['why']   = 'it runs other abilities without the bridge\'s checks';
		return $p;
	}
	$action = substr( (string) $name, strpos( (string) $name, '/' ) + 1 );
	$table  = wpu_bt_guard_table( $builder );
	if ( ! isset( $table[ $action ] ) ) {
		$p['class'] = 'blocked';
		$p['why']   = 'it is not on the list of builder actions this version of WPU Bridge has checked';
		return $p;
	}
	$p['class']    = $table[ $action ][0];
	$p['why']      = isset( $table[ $action ][1] ) ? $table[ $action ][1] : '';
	$p['post_arg'] = isset( $table[ $action ][2] ) ? $table[ $action ][2] : '';
	return $p;
}

/** Is the "builder AI actions" switch on? */
function wpu_bt_guard_switch() {
	return (bool) wpu_bt_setting( 'builder_abilities' );
}

/* -------------------------------------------------------------------------
 * Checking input
 * ---------------------------------------------------------------------- */

/** Decode what a string can turn into: entities and percent-encoding, repeated. */
function wpu_bt_guard_canon( $text ) {
	$text = (string) $text;
	for ( $i = 0; $i < 6; $i++ ) {
		$next = rawurldecode( html_entity_decode( $text, ENT_QUOTES | ENT_HTML5, 'UTF-8' ) );
		if ( $next === $text ) {
			break;
		}
		$text = $next;
	}
	return $text;
}

/** A web address that runs script or carries a document. */
function wpu_bt_guard_bad_address( $value ) {
	$flat = strtolower( preg_replace( '/[\x00-\x20\x7f]+/', '', (string) $value ) );
	if ( false !== strpos( $flat, 'javascript:' ) || false !== strpos( $flat, 'vbscript:' ) || false !== strpos( $flat, 'livescript:' ) ) {
		return true;
	}
	return 0 === strpos( $flat, 'data:' ) && ! preg_match( '/^data:image\/(png|jpe?g|gif|webp|avif);/', $flat );
}

/** Parse HTML properly and report the first thing that can run script, or ''. */
function wpu_bt_guard_html_reason( $html ) {
	if ( false === strpos( $html, '<' ) ) {
		return '';
	}
	if ( preg_match( '/<\?|<%/', $html ) ) {
		return 'PHP or processing-instruction tags';
	}
	// Builders re-read HTML with other parsers (Breakdance strips CDATA markers, then uses libxml), so a tag
	// can be hidden from one parser and seen by another. Refuse the markers, and also look for dangerous tag
	// names and handlers with a deliberately loose pattern, whatever the proper parser makes of them.
	if ( preg_match( '/<!\[|\]\]>|<!doctype|<\s*\/?\s*(script|iframe|object|embed|applet|base|meta|link|frame|frameset|form|portal)\b/i', $html ) ) {
		return 'markup the bridge does not write (CDATA, doctype, or a script, frame, embed or form tag)';
	}
	if ( preg_match( '/[\s\/"\'`]on[a-z]{3,}\s*=/i', $html ) ) {
		return 'an event handler attribute (on...=)';
	}
	if ( ! class_exists( 'WP_HTML_Tag_Processor' ) ) {
		return 'HTML, which this WordPress version cannot check';
	}
	$p = new WP_HTML_Tag_Processor( $html );
	while ( $p->next_tag( array( 'tag_closers' => 'visit' ) ) ) {
		$tag = strtolower( (string) $p->get_tag() );
		if ( in_array( $tag, array( 'script', 'object', 'embed', 'applet', 'base', 'meta', 'link', 'frame', 'frameset', 'iframe', 'form', 'portal', 'noembed', 'xmp', 'plaintext', 'listing' ), true ) ) {
			return 'a <' . $tag . '> tag';
		}
		if ( $p->is_tag_closer() ) {
			continue;
		}
		foreach ( (array) $p->get_attribute_names_with_prefix( '' ) as $n ) {
			$n = strtolower( (string) $n );
			if ( 0 === strpos( $n, 'on' ) || in_array( $n, array( 'srcdoc', 'formaction' ), true ) || ! preg_match( '/^[a-z_:][a-z0-9_:.\-]*\z/', $n ) ) {
				return 'the attribute "' . sanitize_text_field( $n ) . '"';
			}
			$v = $p->get_attribute( $n );
			if ( is_string( $v ) && wpu_bt_guard_bad_address( $v ) ) {
				return 'a javascript: or data: address';
			}
			if ( is_string( $v ) && 'style' === $n && preg_match( '/expression\s*\(|-moz-binding|behavior\s*:|@import/i', $v ) ) {
				return 'script inside CSS';
			}
		}
	}
	// A tag left open at the end would be completed by whatever the builder prints next.
	if ( method_exists( $p, 'paused_at_incomplete_token' ) ? $p->paused_at_incomplete_token() : ( strrpos( $html, '<' ) > (int) strrpos( $html, '>' ) ) ) {
		return 'an unfinished HTML tag';
	}
	return '';
}

/** Why a text value is refused, or ''. Checked as given and in decoded form. */
function wpu_bt_guard_text_reason( $value ) {
	$value = (string) $value;
	if ( '' === $value ) {
		return '';
	}
	foreach ( array_unique( array( $value, wpu_bt_guard_canon( $value ) ) ) as $c ) {
		if ( preg_match( '/(breakdance|oxygen)_dynamic|bd-(params|query)\b|\bphpreturn\b|\bprocess_value\b/i', $c ) ) {
			return 'builder dynamic data, which can run code (set it in the builder)';
		}
		if ( false !== strpos( $c, ']]>' ) || false !== stripos( $c, '<![' ) ) {
			return 'CDATA markers';
		}
		if ( preg_match( '/^\s*custom-php\s*\z/i', $c ) ) {
			return 'a PHP condition';
		}
		$r = wpu_bt_guard_html_reason( $c );
		if ( '' !== $r ) {
			return $r;
		}
		if ( preg_match( '/^(javascript|vbscript|livescript|data):/i', preg_replace( '/[\x00-\x20\x7f]+/', '', $c ) ) && wpu_bt_guard_bad_address( $c ) ) {
			return 'a javascript: or data: address';
		}
		if ( preg_match( '/url\(\s*["\']?\s*(javascript|vbscript|data\s*:\s*text)|expression\s*\(|-moz-binding|behavior\s*:\s*url|@import/i', $c ) ) {
			return 'script or an import inside CSS';
		}
	}
	return '';
}

/** fooBar / foo-bar -> foo_bar, lower case. */
function wpu_bt_guard_key( $key ) {
	return strtolower( preg_replace( '/[^A-Za-z0-9]+/', '_', preg_replace( '/([a-z0-9])([A-Z])/', '$1_$2', (string) $key ) ) );
}

/**
 * Walk the whole input. Returns '' when clean, or a sentence naming the first thing that is not allowed.
 */
function wpu_bt_guard_scan( $value, $builder, $path = 'input', $depth = 0, &$budget = null ) {
	if ( null === $budget ) {
		$budget = 60000;
	}
	if ( $depth > 60 || --$budget < 0 ) {
		return 'the input is too large or too deeply nested to check';
	}
	if ( is_object( $value ) ) {
		$value = (array) $value;
	}
	if ( is_string( $value ) ) {
		$r = wpu_bt_guard_text_reason( $value );
		if ( '' !== $r ) {
			return $path . ' holds ' . $r;
		}
		// A JSON document passed as text.
		$t = ltrim( $value, " \t\n\r\0\x0B\xEF\xBB\xBF" );
		if ( '' !== $t && ( '{' === $t[0] || '[' === $t[0] || '"' === $t[0] ) ) {
			if ( strlen( $t ) > MB_IN_BYTES ) {
				return $path . ' is too large to check';
			}
			$j = json_decode( $t, true );
			if ( is_array( $j ) || ( is_string( $j ) && $j !== $value ) ) {
				return wpu_bt_guard_scan( $j, $builder, $path, $depth + 1, $budget );
			}
		}
		return '';
	}
	if ( ! is_array( $value ) ) {
		return '';
	}
	$in_attrs = (bool) preg_match( '/attr/i', $path );
	foreach ( $value as $k => $v ) {
		$key = wpu_bt_guard_key( $k );
		$p   = $path . '.' . preg_replace( '/[^A-Za-z0-9_\-]/', '', (string) $k );
		$tok = explode( '_', $key );
		if ( is_string( $v ) ) {
			$c = wpu_bt_guard_canon( $v );
			// Element and block types.
			if ( in_array( $key, array( 'type', 'element_type', 'slug', 'el_type' ), true ) ) {
				$last = strtolower( preg_replace( '/^.*\\\\/', '', trim( $c ) ) );
				if ( false !== strpos( $c, '\\' ) && preg_match( '/code|shortcode|widget|analyticswpevent|termloopbuilder|oembed|facebook|twitter|instagram|googlemap/', $last ) ) {
					return $p . ' is the "' . sanitize_text_field( $v ) . '" element, which holds code or runs unchecked output (add it by hand in the builder)';
				}
				if ( 'seedprod' === $builder && ( ! preg_match( '/^[a-z0-9\-]{1,40}\z/', $c ) || preg_match( '/html|shortcode|templatetag|widget|script|code/', $c ) ) ) {
					return $p . ' is a "' . sanitize_text_field( $v ) . '" block, which the bridge does not write';
				}
				if ( preg_match( '/javascript|(^|[_\-])js([_\-]|$)|php/i', $c ) ) {
					return $p . ' names something that runs code';
				}
			}
			// Conditions and interaction actions that run code or set attributes.
			if ( in_array( $key, array( 'rule_slug', 'rule_dynamic', 'action', 'trigger', 'active' ), true ) && preg_match( '/php|javascript|(^|[_\-])js([_\-]|$)|attribute/i', $c ) ) {
				return $p . ' ("' . sanitize_text_field( $v ) . '") runs code or sets attributes';
			}
			if ( '' !== trim( $v ) ) {
				// Settings whose name marks them as code.
				if ( array_intersect( $tok, array( 'php', 'javascript', 'js', 'script', 'scripts', 'eval' ) ) || in_array( $key, array( 'code', 'term_query', 'process_value', 'raw_html', 'custom_html', 'html_code', 'header_code', 'footer_code', 'custom_code', 'embed_code', 'tracking_code', 'function_name', 'callback' ), true ) ) {
					return $p . ' is a code setting';
				}
				// Ids, tags and classes are printed inside tags without escaping.
				if ( in_array( $key, array( 'id', 'html_id', 'css_id' ), true ) && ! preg_match( '/^[A-Za-z0-9_:.\-]{1,120}\z/', $v ) ) {
					return $p . ' is not a plain id';
				}
				if ( in_array( $key, array( 'tag', 'tags', 'html_tag', 'wrapper_tag' ), true ) && ( ! preg_match( '/^[A-Za-z][A-Za-z0-9]{0,15}\z/', $v ) || in_array( strtolower( $v ), array( 'script', 'style', 'iframe', 'object', 'embed', 'form', 'link', 'meta', 'base', 'svg', 'math', 'template', 'noscript', 'textarea', 'title', 'xmp' ), true ) ) ) {
					return $p . ' is not an allowed tag name';
				}
				if ( array_intersect( $tok, array( 'class', 'classes', 'classname' ) ) && preg_match( '/["\'<>=`]/', $c ) ) {
					return $p . ' is not a plain class name';
				}
				// Attribute names and free-text attribute settings.
				if ( ( $in_attrs && in_array( $key, array( 'name', 'attribute', 'key' ), true ) ) || preg_match( '/attr.*name/', $key ) ) {
					if ( ! preg_match( '/^[A-Za-z_][A-Za-z0-9_:.\-]{0,60}\z/', trim( $c ) ) || preg_match( '/^(on|srcdoc\z|formaction\z|style\z|href\z|src\z|action\z)/i', trim( $c ) ) ) {
						return $p . ' ("' . sanitize_text_field( $v ) . '") is not an attribute the bridge sets';
					}
				}
				if ( preg_match( '/attr/', $key ) && preg_match( '/(^|[\s"\';,\/])(on[a-z]{3,}|srcdoc|formaction)\s*=/i', $c ) ) {
					return $p . ' sets an attribute that runs script';
				}
				if ( in_array( $key, array( 'name', 'attribute', 'key' ), true ) && preg_match( '/^\s*on[a-z]{3,}\s*\z|\son[a-z]{3,}\s*\z/i', $c ) ) {
					return $p . ' names an event handler';
				}
				// Addresses, ids, colours and sizes get printed inside attributes and inline scripts by some
				// elements, so they may not hold anything that could end a quoted string.
				if ( array_intersect( $tok, array( 'url', 'src', 'href', 'link', 'poster', 'color', 'colour', 'width', 'height', 'size', 'speed', 'duration', 'delay', 'id', 'unit', 'number' ) ) && preg_match( '/[\'"`\\\\<>\r\n]/', $c ) ) {
					return $p . ' holds quotes, backslashes or angle brackets, which do not belong in an address, id, colour or size';
				}
				// SeedProd prints these inside its page script.
				if ( 'seedprod' === $builder && ( in_array( $key, array( 'action', 'countdown_type', 'animation', 'easing' ), true ) || preg_match( '/_(duration|delay|speed|type)\z/', $key ) ) && ! preg_match( '/^[A-Za-z0-9_\- .#%]{0,60}\z/', $v ) ) {
					return $p . ' must be a plain word or number';
				}
			}
		}
		if ( true === $v && 'load_terms_by_query' === $key ) {
			return $p . ' switches on a PHP query';
		}
		$r = wpu_bt_guard_scan( $v, $builder, $p, $depth + 1, $budget );
		if ( '' !== $r ) {
			return $r;
		}
	}
	return '';
}

/** Does the input set where a form sends things, anywhere inside it? */
function wpu_bt_guard_has_destination( $value, $depth = 0 ) {
	if ( $depth > 40 || ! ( is_array( $value ) || is_object( $value ) ) ) {
		return false;
	}
	foreach ( (array) $value as $k => $v ) {
		$key = wpu_bt_guard_key( $k );
		if ( ( in_array( $key, array( 'webhook_url', 'emails', 'email_to', 'recipient', 'recipients', 'redirect_url', 'bcc', 'cc' ), true ) || false !== strpos( $key, 'webhook' ) ) && ! empty( $v ) ) {
			return true;
		}
		if ( wpu_bt_guard_has_destination( $v, $depth + 1 ) ) {
			return true;
		}
	}
	return false;
}

/** Why changing this post is a live or site-wide change, or ''. */
function wpu_bt_guard_live_reason( $id ) {
	$p = get_post( $id );
	if ( ! $p ) {
		return '';
	}
	if ( 0 === strpos( $p->post_type, 'breakdance_' ) || 0 === strpos( $p->post_type, 'oxygen_' ) || get_post_meta( $id, '_seedprod_is_theme_template', true ) ) {
		return 'this is a template, header, footer, popup or reusable block that appears on many pages';
	}
	if ( in_array( $p->post_status, array( 'publish', 'private', 'future' ), true ) ) {
		return 'this page is live';
	}
	return '';
}

/** Reasons this call needs the person's go-ahead ('' when it does not). */
function wpu_bt_guard_confirm_reason( $name, array $policy, $input ) {
	if ( 'confirm' === $policy['class'] ) {
		return $policy['why'];
	}
	$in = (array) $input;
	if ( 'seedprod/save-page' === $name ) {
		if ( ! empty( $in['activate'] ) ) {
			return 'it switches this page on as the site\'s coming soon, maintenance, login or 404 page';
		}
		if ( isset( $in['type'] ) && in_array( (string) $in['type'], array( 'header', 'footer', 'page-template', 'part' ), true ) ) {
			return 'a theme template applies to many pages at once';
		}
	}
	if ( 'seedprod/save-page' === $name && ! empty( $in['id'] ) ) {
		// SeedProd's coming soon, maintenance, login and 404 pages are live through a setting, whatever their status.
		foreach ( array( 'seedprod_coming_soon_page_id', 'seedprod_maintenance_mode_page_id', 'seedprod_login_page_id', 'seedprod_404_page_id' ) as $opt ) {
			if ( absint( get_option( $opt ) ) === absint( $in['id'] ) ) {
				return 'this is the page SeedProd shows as the site\'s coming soon, maintenance, login or 404 page';
			}
		}
	}
	if ( isset( $in['status'] ) && in_array( (string) $in['status'], array( 'publish', 'private', 'future' ), true ) ) {
		return 'it publishes the page';
	}
	if ( wpu_bt_guard_has_destination( $input ) ) {
		return 'it sets where a form sends what visitors enter';
	}
	if ( '' !== $policy['post_arg'] && ! empty( $in[ $policy['post_arg'] ] ) ) {
		return wpu_bt_guard_live_reason( absint( $in[ $policy['post_arg'] ] ) );
	}
	return '';
}

/** One-time code tied to this person, this ability and this exact input. Valid for 10 to 20 minutes. */
function wpu_bt_guard_token( $name, $input, $window = 0 ) {
	$slot = (int) floor( time() / 600 ) - $window;
	return substr( hash_hmac( 'sha256', get_current_user_id() . '|' . $name . '|' . md5( (string) wp_json_encode( $input ) ) . '|' . $slot, wp_salt( 'auth' ) ), 0, 16 );
}

/* -------------------------------------------------------------------------
 * Undo for builder abilities
 * ---------------------------------------------------------------------- */

function wpu_bt_guard_meta_prefix( $builder ) {
	return in_array( $builder, array( 'seedprod', 'oxygen' ), true ) ? '_' . $builder . '_' : '_breakdance_';
}

/** Everything a builder ability can change on one post, as stored. Null when it is too large to keep. */
function wpu_bt_guard_snapshot( $id, $builder, $with_status = false ) {
	global $wpdb;
	$p = get_post( $id );
	if ( ! $p ) {
		return null;
	}
	$prefix = wpu_bt_guard_meta_prefix( $builder );
	// Fixed table name from $wpdb; values are prepared.
	$rows = $wpdb->get_results( $wpdb->prepare( "SELECT meta_key, meta_value FROM {$wpdb->postmeta} WHERE post_id = %d AND meta_key LIKE %s ORDER BY meta_id ASC", $id, $wpdb->esc_like( $prefix ) . '%' ), ARRAY_A ); // phpcs:ignore WordPress.DB.DirectDatabaseQuery
	$meta = array();
	$size = 0;
	foreach ( (array) $rows as $r ) {
		if ( ! isset( $meta[ $r['meta_key'] ] ) ) {
			$meta[ $r['meta_key'] ] = $r['meta_value'];
			$size                  += strlen( (string) $r['meta_value'] );
		}
	}
	if ( $size + strlen( $p->post_content ) + strlen( $p->post_content_filtered ) > 6 * MB_IN_BYTES ) {
		return null;
	}
	// The status is only put back when this call was about the status: undoing a text edit made while the
	// page was a draft must not unpublish it later.
	$fields = array( 'post_title' => $p->post_title, 'post_content' => $p->post_content, 'post_content_filtered' => $p->post_content_filtered, 'menu_order' => $p->menu_order );
	if ( $with_status ) {
		$fields['post_status'] = $p->post_status;
	}
	return array(
		'kind'  => 'multi',
		'items' => array(
			array( 'kind' => 'post', 'id' => $id, 'fields' => $fields ),
			array( 'kind' => 'builder_meta', 'id' => $id, 'builder' => $builder, 'values' => $meta ),
		),
	);
}

/** Undo kind "builder_meta": put a builder's own meta on a post back exactly as it was. */
function wpu_bt_guard_meta_restore( array $p ) {
	global $wpdb;
	$id      = absint( $p['id'] );
	$builder = isset( $p['builder'] ) && in_array( $p['builder'], array( 'seedprod', 'oxygen' ), true ) ? $p['builder'] : 'breakdance';
	if ( ! get_post( $id ) || ! current_user_can( 'edit_post', $id ) ) {
		return wpu_bt_err( 'Post ' . $id . ' is gone or you cannot edit it.' );
	}
	$prefix = wpu_bt_guard_meta_prefix( $builder );
	$before = array();
	foreach ( (array) $p['values'] as $k => $raw ) {
		if ( 0 === strpos( (string) $k, $prefix ) && is_string( $raw ) ) {
			$before[ (string) $k ] = $raw;
		}
	}
	// Fixed table name from $wpdb; values are prepared.
	$now = $wpdb->get_col( $wpdb->prepare( "SELECT DISTINCT meta_key FROM {$wpdb->postmeta} WHERE post_id = %d AND meta_key LIKE %s", $id, $wpdb->esc_like( $prefix ) . '%' ) ); // phpcs:ignore WordPress.DB.DirectDatabaseQuery
	foreach ( (array) $now as $k ) {
		if ( ! isset( $before[ $k ] ) ) {
			delete_post_meta( $id, $k );
		}
	}
	foreach ( $before as $k => $raw ) {
		wpu_bt_meta_raw_restore( $id, $k, $raw );
	}
	clean_post_cache( $id );
	if ( 'seedprod' !== $builder && function_exists( '\Breakdance\Render\generateCacheForPost' ) ) {
		try {
			\Breakdance\Render\generateCacheForPost( $id );
		} catch ( Throwable $e ) {
			unset( $e ); // the builder rebuilds its CSS on the next save
		}
	}
	return array( 'post' => $id, 'restored' => count( $before ) );
}

/* -------------------------------------------------------------------------
 * Before and after a call
 * ---------------------------------------------------------------------- */

/**
 * Check one ability call before it runs.
 * @return WP_Error|array{policy:array,undo:?array,post:int}
 */
function wpu_bt_guard_before( $name, $input, $token, $via_readonly_tool ) {
	$policy = wpu_bt_guard_policy( $name );
	$out    = array( 'policy' => $policy, 'undo' => null, 'post' => 0 );
	if ( '' === $policy['builder'] ) {
		return $out;
	}
	if ( 'blocked' === $policy['class'] ) {
		return wpu_bt_err( $name . ' is not run through WPU Bridge: ' . $policy['why'] . '.' );
	}
	if ( 'read' === $policy['class'] ) {
		return $out;
	}
	if ( ! wpu_bt_guard_switch() ) {
		return wpu_bt_err( $name . ' is switched off. An administrator can allow this builder\'s AI actions under Tools > WPU Bridge ("Builder AI actions"). Until then, only look-ups such as the page tree work.' );
	}
	if ( 'look' === $policy['class'] ) {
		return $out;
	}
	if ( $via_readonly_tool ) {
		return wpu_bt_err( $name . ' changes things: use ability_run.' );
	}
	$found = wpu_bt_guard_scan( $input, $policy['builder'] );
	if ( '' !== $found ) {
		return wpu_bt_err( 'Not run: ' . $found . '. WPU Bridge does not write code, scripts, embeds or dynamic data through a builder; those are added by hand in the builder.' );
	}
	$in = (array) $input;
	$id = '' !== $policy['post_arg'] && isset( $in[ $policy['post_arg'] ] ) ? absint( $in[ $policy['post_arg'] ] ) : 0;
	if ( $id ) {
		$p = get_post( $id );
		if ( ! $p || ! current_user_can( 'edit_post', $id ) || 'revision' === $p->post_type ) {
			return wpu_bt_err( 'No post ' . $id . ' that you can edit.' );
		}
		if ( ! function_exists( 'wp_check_post_lock' ) ) {
			require_once ABSPATH . 'wp-admin/includes/post.php';
		}
		$locker = wp_check_post_lock( $id );
		if ( $locker ) {
			$u = get_userdata( $locker );
			return wpu_bt_err( ( $u ? $u->display_name : 'Someone' ) . ' has this page open for editing right now. Try again when they have finished.' );
		}
	}
	$why = wpu_bt_guard_confirm_reason( $name, $policy, $input );
	if ( '' !== $why ) {
		$token = is_string( $token ) ? trim( $token ) : '';
		if ( '' === $token || ! ( hash_equals( wpu_bt_guard_token( $name, $input ), $token ) || hash_equals( wpu_bt_guard_token( $name, $input, 1 ), $token ) ) ) {
			return wpu_bt_err( 'This needs the person\'s go-ahead first: ' . $why . '. Tell them exactly what will change. Only when they agree, call ability_run again with the same name and input and "confirm_token": "' . wpu_bt_guard_token( $name, $input ) . '" (valid for 10 minutes, for this exact request only).' );
		}
	}
	if ( $id ) {
		$out['post'] = $id;
		$out['undo'] = wpu_bt_guard_snapshot( $id, $policy['builder'], isset( $in['status'] ) );
		if ( null === $out['undo'] ) {
			return wpu_bt_err( 'This page is too large for the bridge to keep a copy for undo, so it is not changed here.' );
		}
	}
	return $out;
}

/** Record the change after a builder ability ran. Returns a change id or ''. */
function wpu_bt_guard_after( $name, array $before, $result ) {
	$policy = $before['policy'];
	if ( '' === $policy['builder'] || ! in_array( $policy['class'], array( 'write', 'confirm' ), true ) ) {
		return '';
	}
	if ( $before['post'] && $before['undo'] ) {
		return (string) wpu_bt_change_add( 'ability_run', $name . ' on #' . $before['post'] . ' "' . get_the_title( $before['post'] ) . '"', $before['undo'] );
	}
	$action = substr( $name, strpos( $name, '/' ) + 1 );
	if ( ! $before['post'] && ( 0 === strpos( $action, 'create-' ) || 'save-page' === $action ) ) {
		$res = is_object( $result ) ? (array) $result : $result;
		$new = 0;
		foreach ( array( 'post_id', 'id', 'ID' ) as $k ) {
			if ( is_array( $res ) && isset( $res[ $k ] ) && is_numeric( $res[ $k ] ) ) {
				$new = absint( $res[ $k ] );
				break;
			}
		}
		if ( $new && get_post( $new ) ) {
			return (string) wpu_bt_change_add( 'ability_run', $name . ' created #' . $new . ' "' . get_the_title( $new ) . '"', array( 'kind' => 'trash', 'id' => $new ) );
		}
	}
	return '';
}
