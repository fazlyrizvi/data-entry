import React, { useMemo } from 'react'
import EChartsReact from 'echarts-for-react'
import * as echarts from 'echarts'

export const ProcessingChart: React.FC = () => {
  const option = useMemo(() => ({
    title: {
      text: 'Processing Throughput (24h)',
      left: 'left',
      textStyle: {
        fontSize: 16,
        fontWeight: 600,
        color: '#171717'
      }
    },
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(255, 255, 255, 0.9)',
      borderColor: 'rgba(0, 0, 0, 0.1)',
      textStyle: {
        color: '#171717'
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: ['00:00', '02:00', '04:00', '06:00', '08:00', '10:00', '12:00', '14:00', '16:00', '18:00', '20:00', '22:00'],
      axisLine: {
        lineStyle: {
          color: '#E5E5E5'
        }
      },
      axisLabel: {
        color: '#A3A3A3'
      }
    },
    yAxis: {
      type: 'value',
      axisLine: {
        lineStyle: {
          color: '#E5E5E5'
        }
      },
      axisLabel: {
        color: '#A3A3A3'
      },
      splitLine: {
        lineStyle: {
          color: '#F5F5F5'
        }
      }
    },
    series: [
      {
        name: 'Jobs Processed',
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        lineStyle: {
          color: '#0066FF',
          width: 3
        },
        itemStyle: {
          color: '#0066FF',
          borderColor: '#ffffff',
          borderWidth: 2
        },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            {
              offset: 0,
              color: 'rgba(0, 102, 255, 0.2)'
            },
            {
              offset: 1,
              color: 'rgba(0, 102, 255, 0.02)'
            }
          ])
        },
        data: [65, 78, 90, 81, 125, 142, 138, 156, 145, 128, 95, 72]
      }
    ]
  }), [])

  return (
    <div className="h-80">
      <EChartsReact
        option={option}
        style={{ height: '100%', width: '100%' }}
        opts={{ renderer: 'canvas' }}
      />
    </div>
  )
}