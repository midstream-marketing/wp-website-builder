<?php
/**
 * Plugin Name: WPU SEO Schema
 * Description: Prints the JSON-LD stored in a page's _wpu_schema field (written by WP Ultimate Build).
 *              Permanent and tiny: it stays after the WPU Bridge is removed. Install as an mu-plugin.
 * Version:     1.0.0
 * Author:      Webelite Digital
 *
 * Why a separate file: the bridge expires and deletes itself, but schema has to keep printing.
 *
 * Safety: the value is JSON that only an administrator can write (through the bridge or
 * update_post_meta). It is decoded and re-encoded here, never echoed raw, and the encoder
 * escapes "<", ">" and "&" so a stored string cannot close the <script> element.
 */

defined( 'ABSPATH' ) || exit;

add_action( 'wp_head', 'wpu_seo_schema_print', 30 );

function wpu_seo_schema_print() {
	if ( ! is_singular() ) {
		return;
	}
	$raw = get_post_meta( get_queried_object_id(), '_wpu_schema', true );
	if ( ! is_string( $raw ) || '' === $raw ) {
		return;
	}
	$data = json_decode( $raw, true );
	if ( ! is_array( $data ) || ! $data ) {
		return;
	}
	// A list of nodes becomes one @graph so there is a single script element.
	if ( array_keys( $data ) === range( 0, count( $data ) - 1 ) ) {
		$data = array(
			'@context' => 'https://schema.org',
			'@graph'   => array_values( $data ),
		);
	}
	$json = wp_json_encode( $data, JSON_HEX_TAG | JSON_HEX_AMP | JSON_HEX_APOS | JSON_HEX_QUOT | JSON_UNESCAPED_SLASHES );
	if ( false === $json ) {
		return;
	}
	echo "\n<script type=\"application/ld+json\" class=\"wpu-schema\">" . $json . "</script>\n"; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped -- JSON encoded with HEX flags above.
}
