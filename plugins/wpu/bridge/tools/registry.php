<?php
/**
 * Tool registry for the bridge's typed tools (/tools and /tool).
 *
 * A tool is a named, fixed action with checked arguments: page content, Gutenberg blocks, page builders
 * (Elementor, Divi, Bricks, Beaver Builder, Breakdance, SeedProd), WooCommerce, ACF, updates and draft
 * themes. Unlike /run, a tool never executes code it is sent. Writes are logged with the team member's
 * name and almost all can be undone (change_undo).
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

$GLOBALS['wpu_bt_tools'] = array();

/**
 * @param string $name tool name
 * @param array  $def  title, description, props (JSON-schema properties), required (list),
 *                     write (bool), destructive (bool), idempotent (bool), cap (capability),
 *                     group ('' | 'updates' | 'orders'), available (callable|null), run (callable)
 */
function wpu_bt_define_tool( $name, array $def ) {
	$GLOBALS['wpu_bt_tools'][ $name ] = array_merge( array(
		'title'       => $name,
		'description' => '',
		'props'       => array(),
		'required'    => array(),
		'write'       => false,
		'destructive' => false,
		'idempotent'  => false,
		'cap'         => 'manage_options',
		'group'       => '',
		'available'   => null,
		'run'         => null,
	), $def );
}

/** Tools this site offers right now (depends on active plugins and the bridge's switches). */
function wpu_bt_tools_available() {
	$s   = wpu_bt_settings();
	$out = array();
	foreach ( $GLOBALS['wpu_bt_tools'] as $name => $t ) {
		if ( $t['write'] && $s['read_only'] ) {
			continue;
		}
		if ( 'updates' === $t['group'] && ! $s['allow_updates'] ) {
			continue;
		}
		if ( 'orders' === $t['group'] && $t['write'] && ! $s['allow_orders'] ) {
			continue;
		}
		if ( 'themes' === $t['group'] && ! $s['allow_themes'] ) {
			continue;
		}
		if ( is_callable( $t['available'] ) && ! call_user_func( $t['available'] ) ) {
			continue;
		}
		$out[ $name ] = $t;
	}
	return $out;
}

function wpu_bt_tool_schema( $name, array $t ) {
	$props = $t['props'] ? $t['props'] : new stdClass();
	$tool  = array(
		'name'        => $name,
		'title'       => $t['title'],
		'description' => $t['description'],
		'inputSchema' => array(
			'type'                 => 'object',
			'properties'           => $props,
			'additionalProperties' => false,
		),
		'annotations' => array(
			'title'           => $t['title'],
			'readOnlyHint'    => ! $t['write'],
			'destructiveHint' => (bool) $t['destructive'],
			'idempotentHint'  => (bool) $t['idempotent'] || ! $t['write'],
			'openWorldHint'   => false,
		),
	);
	if ( $t['required'] ) {
		$tool['inputSchema']['required'] = array_values( $t['required'] );
	}
	return $tool;
}

/** Light schema check: required keys, unknown keys, basic types and enums at the top level. */
function wpu_bt_check_args( array $t, $args ) {
	if ( null === $args ) {
		$args = array();
	}
	if ( ! is_array( $args ) || ( $args && array_keys( $args ) === range( 0, count( $args ) - 1 ) ) ) {
		return new WP_Error( 'args', 'arguments must be an object.' );
	}
	foreach ( $t['required'] as $r ) {
		if ( ! array_key_exists( $r, $args ) || null === $args[ $r ] || '' === $args[ $r ] ) {
			return new WP_Error( 'args', 'Missing required argument: ' . $r );
		}
	}
	foreach ( $args as $k => $v ) {
		if ( ! isset( $t['props'][ $k ] ) ) {
			return new WP_Error( 'args', 'Unknown argument: ' . $k . '. Known: ' . implode( ', ', array_keys( $t['props'] ) ) );
		}
		$type = isset( $t['props'][ $k ]['type'] ) ? $t['props'][ $k ]['type'] : null;
		$ok   = true;
		$v_is_list = is_array( $v ) && ( ! $v || array_keys( $v ) === range( 0, count( $v ) - 1 ) );
		switch ( $type ) {
			case 'string':
				$ok = is_string( $v ) || is_int( $v ) || is_float( $v );
				break;
			case 'integer':
				$ok = is_int( $v ) || ( is_string( $v ) && preg_match( '/^-?\d+$/', $v ) ) || ( is_float( $v ) && floor( $v ) === $v );
				break;
			case 'number':
				$ok = is_numeric( $v );
				break;
			case 'boolean':
				$ok = is_bool( $v ) || in_array( $v, array( 'true', 'false', 0, 1, '0', '1' ), true );
				break;
			case 'array':
				$ok = $v_is_list;
				break;
			case 'object':
				$ok = is_array( $v ) && ( ! $v || ! $v_is_list );
				break;
		}
		if ( ! $ok ) {
			return new WP_Error( 'args', 'Argument ' . $k . ' must be ' . ( 'integer' === $type ? 'an ' : 'a ' ) . $type . '.' );
		}
		if ( isset( $t['props'][ $k ]['enum'] ) && ! in_array( $v, $t['props'][ $k ]['enum'], true ) ) {
			return new WP_Error( 'args', 'Argument ' . $k . ' must be one of: ' . implode( ', ', $t['props'][ $k ]['enum'] ) );
		}
	}
	return $args;
}

/**
 * Run one tool for the signed-in bridge user.
 * @return mixed|WP_Error the tool's result
 */
function wpu_bt_call( $name, $args, $apply ) {
	$name  = (string) $name;
	$avail = wpu_bt_tools_available();
	if ( ! isset( $avail[ $name ] ) ) {
		return wpu_bt_err( isset( $GLOBALS['wpu_bt_tools'][ $name ] ) ? 'Tool ' . $name . ' is switched off on this site (Tools > WPU Bridge) or needs a plugin that is not active.' : 'Unknown tool: ' . $name . '. GET /tools lists them.' );
	}
	$t    = $avail[ $name ];
	$args = wpu_bt_check_args( $t, $args );
	if ( is_wp_error( $args ) ) {
		return $args;
	}
	if ( ! current_user_can( $t['cap'] ) ) {
		wpu_bt_record( 'tool:' . $name, array( 'refused' => 'capability' ), false );
		return wpu_bt_err( 'Your WordPress account lacks the ' . $t['cap'] . ' capability needed for ' . $name . '.' );
	}
	// The team's rule: nothing changes a site without "apply". Without it, a tool that has a dry run is
	// forced into one (whatever dry_run was sent as), and a tool that has none is refused.
	if ( isset( $t['props']['dry_run'] ) && array_key_exists( 'dry_run', $args ) ) {
		$args['dry_run'] = (bool) filter_var( $args['dry_run'], FILTER_VALIDATE_BOOLEAN );
	}
	if ( $t['write'] && ! $apply ) {
		if ( ! isset( $t['props']['dry_run'] ) ) {
			wpu_bt_record( 'tool:' . $name, array( 'refused' => 'no apply' ), false );
			return wpu_bt_err( $name . ' changes the site. Show the person what will change, then run it again with "apply".' );
		}
		$args['dry_run'] = true;
	}
	if ( function_exists( 'set_time_limit' ) ) {
		@set_time_limit( 300 ); // phpcs:ignore WordPress.PHP.NoSilencedErrors -- not allowed on some hosts
	}
	try {
		$out = call_user_func( $t['run'], $args );
	} catch ( Throwable $e ) {
		$out = wpu_bt_err( 'The tool failed: ' . $e->getMessage() );
	}
	if ( $t['write'] || is_wp_error( $out ) ) {
		$brief = array();
		foreach ( array( 'id', 'ids', 'post_id', 'plugins', 'themes', 'change_id', 'dry_run', 'name' ) as $k ) {
			if ( isset( $args[ $k ] ) ) {
				$brief[ $k ] = is_array( $args[ $k ] ) ? array_slice( $args[ $k ], 0, 10 ) : $args[ $k ];
			}
		}
		if ( ! empty( $args['confirm_token'] ) ) {
			$brief['with_go_ahead'] = true;
		}
		if ( is_wp_error( $out ) ) {
			$brief['error'] = substr( $out->get_error_message(), 0, 200 );
		} elseif ( is_array( $out ) && isset( $out['change_id'] ) ) {
			$brief['change_id'] = $out['change_id'];
		}
		$brief['apply'] = (bool) $apply;
		wpu_bt_record( 'tool:' . $name, $brief, ! is_wp_error( $out ) );
		if ( $apply && ! is_wp_error( $out ) ) {
			wpu_bridge_record( 'tool:' . $name, 0, $brief ); // changes also go in the bridge's own audit
		}
	}
	return $out;
}
