jQuery(document).ready(function(){

    jQuery(window).on('load', function() {
        var sticky_scrollTop_init = jQuery(this).scrollTop();
        if ( sticky_scrollTop_init>0 ){
            jQuery('.elementor-location-header .elementor-sticky--active').addClass('bg-color-blk');
        } 
    });


    jQuery(window).on('scroll', function() {
        // console.log('scrolling2');
        var sticky_scrollTop = jQuery(this).scrollTop();
        if ( sticky_scrollTop>0 ){
            jQuery('.elementor-location-header .elementor-sticky--active').addClass('bg-color-blk');
        }else{
            jQuery('.elementor-location-header .elementor-sticky--active').removeClass('bg-color-blk');
        }
    });
});