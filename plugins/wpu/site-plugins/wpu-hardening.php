<?php
/**
 * Plugin Name: WPU Hardening
 * Description: Small, switchable hardening measures set by WP Ultimate Build. Every measure is OFF
 *              until turned on in the wpu_hardening option (php/hardening-set.php), so installing
 *              this file changes nothing by itself. Install as an mu-plugin.
 * Version:     1.0.0
 * Author:      Webelite Digital
 *
 * Measures (option keys):
 *   no_file_edit      - DISALLOW_FILE_EDIT: no theme/plugin code editor in wp-admin
 *   no_xmlrpc         - turn off XML-RPC (breaks Jetpack and the WordPress mobile app - ask first)
 *   no_user_listing   - /wp/v2/users answers only to logged-in users who may list users
 *   no_author_scan    - ?author=N no longer redirects to /author/<login>/ (login names stay private)
 *   hide_version      - drop the WordPress version from <head> and feeds
 *   headers           - X-Content-Type-Options, Referrer-Policy, X-Frame-Options, Permissions-Policy
 *
 * Deliberately not here: login URL changes, IP blocking, rate limiting, malware scanning - the
 * site's security plugin (Wordfence, Solid Security...) or the host does those better.
 */

defined( 'ABSPATH' ) || exit;

function wpu_hardening_on( $key ) {
	static $opts = null;
	if ( null === $opts ) {
		$opts = get_option( 'wpu_hardening', array() );
		$opts = is_array( $opts ) ? $opts : array();
	}
	return ! empty( $opts[ $key ] );
}

if ( wpu_hardening_on( 'no_file_edit' ) && ! defined( 'DISALLOW_FILE_EDIT' ) ) {
	define( 'DISALLOW_FILE_EDIT', true );
}

if ( wpu_hardening_on( 'no_xmlrpc' ) ) {
	// xmlrpc_enabled alone still answers system.listMethods and pingbacks; refuse the endpoint outright.
	if ( defined( 'XMLRPC_REQUEST' ) && XMLRPC_REQUEST ) {
		status_header( 403 );
		header( 'Content-Type: text/plain; charset=utf-8' );
		echo 'XML-RPC is disabled on this site.';
		exit;
	}
	add_filter( 'xmlrpc_enabled', '__return_false' );
	add_filter( 'xmlrpc_methods', '__return_empty_array' );
	add_filter( 'wp_headers', function ( $headers ) {
		unset( $headers['X-Pingback'] );
		return $headers;
	} );
}

if ( wpu_hardening_on( 'no_user_listing' ) ) {
	add_filter( 'rest_endpoints', function ( $endpoints ) {
		// edit_posts too: the block editor's author picker calls /wp/v2/users?who=authors as an Editor/Author.
		if ( current_user_can( 'list_users' ) || current_user_can( 'edit_posts' ) ) {
			return $endpoints;
		}
		unset( $endpoints['/wp/v2/users'], $endpoints['/wp/v2/users/(?P<id>[\d]+)'] );
		return $endpoints;
	} );
}

if ( wpu_hardening_on( 'no_author_scan' ) ) {
	add_action( 'template_redirect', function () {
		// Only the bare ?author=N probe; real author archives by slug keep working.
		// Skipped on plain-permalink sites, where ?author=N IS the author archive URL.
		if ( ! is_admin() && get_option( 'permalink_structure' ) && isset( $_GET['author'] ) && ! get_query_var( 'author_name' ) ) { // phpcs:ignore WordPress.Security.NonceVerification.Recommended -- read-only check, no state change
			wp_safe_redirect( home_url( '/' ), 301 );
			exit;
		}
	}, 1 );
}

if ( wpu_hardening_on( 'hide_version' ) ) {
	remove_action( 'wp_head', 'wp_generator' );
	add_filter( 'the_generator', '__return_empty_string' );
}

if ( wpu_hardening_on( 'headers' ) ) {
	add_action( 'send_headers', function () {
		if ( headers_sent() ) {
			return;
		}
		header( 'X-Content-Type-Options: nosniff' );
		header( 'Referrer-Policy: strict-origin-when-cross-origin' );
		header( 'X-Frame-Options: SAMEORIGIN' );
		header( 'Permissions-Policy: camera=(), microphone=(), geolocation=()' );
	} );
}
