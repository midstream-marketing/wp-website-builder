<?php
/** Read-only: find text in post content/excerpt/title and in postmeta (Elementor data included).  rwpphp.ps1 php/find-text.php "needle" ["needle2" ...] */
defined( 'ABSPATH' ) || exit;
global $wpdb;
foreach ( array_slice( (array) $argv, 1 ) as $needle ) {
	$like = '%' . $wpdb->esc_like( $needle ) . '%';
	echo "== \"$needle\"\n";
	foreach ( $wpdb->get_results( $wpdb->prepare( "SELECT ID, post_type, post_status, post_title FROM {$wpdb->posts} WHERE post_status NOT IN ('inherit','auto-draft') AND (post_content LIKE %s OR post_excerpt LIKE %s OR post_title LIKE %s) LIMIT 40", $like, $like, $like ) ) as $r ) {
		printf( "  post #%d %s [%s] %s\n", $r->ID, $r->post_type, $r->post_status, $r->post_title );
	}
	foreach ( $wpdb->get_results( $wpdb->prepare( "SELECT m.post_id, m.meta_key, p.post_type, p.post_title FROM {$wpdb->postmeta} m JOIN {$wpdb->posts} p ON p.ID = m.post_id WHERE p.post_status NOT IN ('inherit','auto-draft','trash') AND m.meta_value LIKE %s LIMIT 40", $like ) ) as $r ) {
		printf( "  meta #%d %s %s (%s)\n", $r->post_id, $r->meta_key, $r->post_type, $r->post_title );
	}
	foreach ( $wpdb->get_results( $wpdb->prepare( "SELECT option_name FROM {$wpdb->options} WHERE option_value LIKE %s AND option_name NOT LIKE '\\_transient%%' LIMIT 20", $like ) ) as $r ) {
		printf( "  option %s\n", $r->option_name );
	}
}
