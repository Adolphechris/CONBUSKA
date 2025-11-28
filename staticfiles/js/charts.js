(function ($) {
    var chartMotifs = echarts.init(document.getElementById('echart-pie-motifs'));
    var chartVisites = echarts.init(document.getElementById('echart-bar-visites'));
    var chartHebdomadaire = echarts.init(document.getElementById('echart-bar-hebdomadaire'));

    // Show title, legends and empty axes
    chartMotifs.setOption({
        title: {
            text: 'Classement des Motifs'
        },
        tooltip: {},
        legend: {},
        toolbox: {
            show: true,
            feature: {
                magicType: {
                    show: true,
                    type: ['pie', 'funnel']
                },
                restore: {
                    show: true,
                    title: "Restore"
                },
                saveAsImage: {
                    show: true,
                    title: "Save Image"
                }
            }
        },
        series: [
            {
                name: 'Motifs',
                type: 'pie',
                roseType: 'area',
                radius: [25, 90],
			    center: ['50%', 170],
			    sort: 'ascending',
                data: []
            }
        ]
    });

    $.getJSON($SCRIPT_ROOT + '/_stats_motifs',
    function(data) {
        var datas = data.stats;
        console.log(datas);
        chartMotifs.setOption({
            tooltip: {
		        trigger: 'item',
				formatter: "{a} <br/>{b} : {c} ({d}%)"
			},
			legend: {
			    x: 'center',
				y: 'bottom',
				data: datas
			},
			calculable: true,
            series: [
                {
                    // Find series by name
                    name: 'Motifs',
                    data: datas
                }
            ]
        });
    });

    chartVisites.setOption({
        title: {},
        legend: {},
        tooltip: {
          trigger: 'axis'
        },
        xAxis: {
            data: ['Janvier', 'Fevrier', 'Mars', 'Avril', 'Mai', 'Juin', 'Juillet', 'Aout', 'Septembre', 'Octobre',
             'Novembre', 'Decembre']
        },
        yAxis: {
            axisTick: {
              length: 6,
              lineStyle: {
                type: 'dashed'
                // ...
              }
            }
        },
        series: [
            {
                type: 'bar',
                data: [],
                barWidth: '40%',
                barGap: '50%',
                barCategoryGap: '80%',
                showBackground: true,
                backgroundStyle: {
                    color: 'rgba(220, 220, 220, 0.8)'
                }
            }
        ]
    });

    $.getJSON($SCRIPT_ROOT + '/_stats_visites',
    function(data) {
        console.log(data.stats);
        chartVisites.setOption({
            series: [
                {
                    data: data.stats
                }
            ]
        });
    });

    chartHebdomadaire.setOption({
        title: {
            text: 'Visites hebdomadaire'
        },
        tooltip: {
            trigger: 'axis',
            axisPointer: {
                type: 'shadow'
            }
        },
        legend: {},
        grid: {
            left: '3%',
            right: '4%',
            bottom: '3%',
            containLabel: true
        },
        xAxis: {
            type: 'value',
            boundaryGap: [0, 0.01]
        },
        yAxis: {
            type: 'category',
            data: ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi']
        },
        series: [
            {
                name: '',
                type: 'bar',
                data: []
            }
        ]
    });

    $.getJSON($SCRIPT_ROOT + '/_stats_hebdomadaire',
    function(data) {
        console.log(data.stats);
        chartHebdomadaire.setOption({
            series: [
                {
                    name: data.stats[1],
                    data: data.stats[0]
                }
            ]
        });
    });
})(jQuery);