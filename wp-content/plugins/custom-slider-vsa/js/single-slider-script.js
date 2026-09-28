jQuery(document).ready(function(){

    jQuery('.single-slider').slick({
        arrows: false,
        dots: true,
        loop: false,
        adaptiveHeight: true,
        infinite: false,
        fade:true
    });

 

    var single_scrollTop_init = jQuery(window).scrollTop(); // Current scroll position
    var single_windowHeight_init = jQuery(window).height(); // Height of the window
    var single_divOffset_init = jQuery('.single-slider-wrapper').offset().top; // Top offset of the div
 

    // Check if the div is in the viewport
    if (single_scrollTop_init + single_windowHeight_init > single_divOffset_init) {
        jQuery('.single-slider-wrapper').addClass('opacity-1'); // Fade in the div
    }

 

    jQuery(window).on('scroll', function() {
        // console.log('scrolling');
        var single_scrollTop = jQuery(this).scrollTop(); // Current scroll position
        var single_windowHeight = jQuery(this).height(); // Height of the window
        var single_divOffset = jQuery('.single-slider-wrapper').offset().top; // Top offset of the div

        // Check if the div is in the viewport
        if (single_scrollTop + single_windowHeight > single_divOffset) {
            jQuery('.single-slider-wrapper').addClass('opacity-1'); // Fade in the div
        }

 
    });

});

