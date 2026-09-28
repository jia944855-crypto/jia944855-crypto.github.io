jQuery(document).ready(function(){

    jQuery('.double-slider').slick({
        arrows: false,
        dots: true,
        adaptiveHeight: true,
        infinite: false
    });

    // Event listener for afterChange
    jQuery('.double-slider').on('afterChange', function(event, slick, currentSlide) {
        jQuery('.double-slider').find('.slick-slide').eq(currentSlide).find('img').addClass('in-view');
    });

 
    

    jQuery('.double-slider-mobile').slick({
        arrows: false,
        dots: true,
        adaptiveHeight: true,
        infinite: false
    });

    var scrollTop_init = jQuery(window).scrollTop(); // Current scroll position
    var windowHeight_init = jQuery(window).height(); // Height of the window
    var divOffset_init = jQuery('.double-slider').offset().top; // Top offset of the div
    var divOffset_init_mobile = jQuery('.double-slider-mobile').offset().top; // Top offset of the div

    // Check if the div is in the viewport
    if (scrollTop_init + windowHeight_init > divOffset_init) {
        jQuery('.double-slider').addClass('opacity-1'); // Fade in the div
        jQuery('.double-slider .slick-active img').addClass('in-view'); // Fade in the div
    }

    // Check if the div is in the viewport
    if (scrollTop_init + windowHeight_init > divOffset_init_mobile) {
        jQuery('.double-slider-mobile').addClass('opacity-1'); // Fade in the div
    }

    jQuery(window).on('scroll', function() {
        // console.log('scrolling');
        var scrollTop = jQuery(this).scrollTop(); // Current scroll position
        var windowHeight = jQuery(this).height(); // Height of the window
        var divOffset = jQuery('.double-slider').offset().top; // Top offset of the div
        var divOffset_mobile = jQuery('.double-slider-mobile').offset().top; // Top offset of the div

        // Check if the div is in the viewport
        if (scrollTop + windowHeight > divOffset) {
            jQuery('.double-slider').addClass('opacity-1'); // Fade in the div
            jQuery('.double-slider .slick-active img').addClass('in-view'); // Fade in the div
        }

        // Check if the div is in the viewport
        if (scrollTop + windowHeight > divOffset_mobile) {
            jQuery('.double-slider-mobile').addClass('opacity-1'); // Fade in the div
        }
    });

});

