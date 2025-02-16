(function ($) {
    $(document).ready(function() {

        $('.js-simple-select').select2();

        function formatTag(tag){
            console.log(tag);
            if(!tag.id){
                return tag.text;
            }
            //var $tag = $( '<span class="label" style="background-color:' + tag.element.value + ';">' + tag.text + '</span>');
            var $tag = $(tag.text);
            return $tag;
        };

        $('.js-select-tags').select2({
            templateResult: formatTag,
            templateSelection: formatTag,
            multiple: true,
            allowClear: true,
            tags: "true"
        });

        // RECHERCHE D'UN PRODUIT
        $('.js-select-produit-ajax').select2({
            ajax:{
                url:'/_search_produit',
                dataType: 'json',
                data: function(params){
                    return{
                        q: params.term,
                    };
                },
                processResults: function(data, params){
                    console.log(data);
                    return {
                        results: $.map(data, function (item) {
                            return {
                                text: item.designation,
                                id: item.designation,
                                cond: item.conditionnements[0],
                                list_cond: item.conditionnements,
                                prix: item.prix,
                                unite: [(item.unite_m, item.unite_m), (item.unite_sm, item.unite_sm)]
                            }
                        })
                    };
                },
                cache: true
            }
        });

        // ACTION A LA SELECTION D'UN PRODUIT
        $('.js-select-produit-ajax').on('select2:select', function (e){
            var data = e.params.data;
            $('.ajax_cond_select').val(data.cond);
            $('.ajax_prix_select').val(data.prix);

            let unite = document.getElementById('unite');
            let optionUniteHTML = '';
            for(let opt of data.unite){
                optionUniteHTML += '<option value ="'  + opt + '">' + opt + '</option>';
            }
            unite.innerHTML = optionUniteHTML;

            //FORMULAIRES QUI ONT UN SELECTFIELD SUR LE CONDITIONNEMENT
            let conditionnements = document.getElementById('conditionnement');
            if(conditionnements.type == 'select-one'){
                let optionCondHTML = '';

                for(let opt of data.list_cond){
                    optionCondHTML += '<option value ="'  + opt + '">' + opt + '</option>';
                }
                conditionnements.innerHTML = optionCondHTML;
            }
        });

        $('.js-select-reference-ajax').select2({
            ajax:{
                url:'/_search_reference',
                dataType: 'json',
                data: function(params){
                    return{
                        q: params.term,
                    };
                },
                processResults: function(data, params){
                    console.log(data);
                    return {
                        results: $.map(data, function (item) {
                            return {
                                text: item.reference,
                                id: item.reference
                            }
                        })
                    };
                },
                cache: true
            }
        });
    })
})(jQuery);