<?php
/**
 * Read-only: find Media Library attachments whose file path contains a fragment.
 * Prints ID, title, alt, dimensions, mime and URL.
 *
 *   powershell -File bin/rwpphp.ps1 php/attachment-lookup.php <file-fragment> [...]
 */

defined( 'ABSPATH' ) || exit;

global $wpdb;
foreach ( array_slice( $argv ?? array(), 1 ) as $frag ) {
	// "#1234" = look up by attachment ID instead of by file name
	$ids = preg_match( '/^#(\d+)$/', $frag, $m )
		? ( get_post_type( (int) $m[1] ) === 'attachment' ? array( (int) $m[1] ) : array() )
		: $wpdb->get_col( $wpdb->prepare(
			"SELECT post_id FROM {$wpdb->postmeta} WHERE meta_key = '_wp_attached_file' AND meta_value LIKE %s",
			'%' . $wpdb->esc_like( $frag ) . '%'
		) );
	printf( "'%s': %d match(es)\n", $frag, count( $ids ) );
	foreach ( $ids as $id ) {
		$m = wp_get_attachment_metadata( $id );
		printf( "  #%-5d %-30s %sx%s %-10s alt=\"%s\"\n        %s\n", $id, mb_strimwidth( get_the_title( $id ), 0, 30 ), $m['width'] ?? '?', $m['height'] ?? '?', get_post_mime_type( $id ), get_post_meta( $id, '_wp_attachment_image_alt', true ), wp_get_attachment_url( $id ) );
	}
}
