<?php
/** Read-only: when were the key pages/templates last modified, and by which revision author? */
defined( 'ABSPATH' ) || exit;
foreach ( array( 2535 => 'Home', 2525 => 'Header tpl', 2527 => 'Footer tpl', 1175 => 'Calculator' ) as $id => $label ) {
	$revs = wp_get_post_revisions( $id, array( 'numberposts' => 1 ) );
	$rev  = $revs ? reset( $revs ) : null;
	printf( "%-11s #%-5d modified %s | last revision %s by %s\n", $label, $id, get_post_field( 'post_modified', $id ), $rev ? $rev->post_modified : '-', $rev ? get_the_author_meta( 'user_login', $rev->post_author ) : '-' );
}
