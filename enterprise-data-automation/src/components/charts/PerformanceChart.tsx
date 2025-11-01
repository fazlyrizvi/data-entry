import React, { useMemo } from 'react'
import EChartsReact from 'echarts-for-react'
import * as echarts from 'echarts'

export const PerformanceChart: React.FC = () => {
  const option = useMemo(() => ({
    title: {
      text: 'Processing Performance Trends',
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
    legend: {
      data: ['Documents Processed', 'Errors'],
      top: 'bottom',
      textStyle: {
        color: '#A3A3A3',
        fontSize: 12
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
      axisLine: {
        lineStyle: {
          color: '#E5E5E5'
        }
      },
      axisLabel: {
        color: '#A3A3A3'
      }
    },
    yAxis: [
      {
        type: 'value',
        name: 'Documents',
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
      {
        type: 'value',
        name: 'Errors',
        axisLine: {
          lineStyle: {
            color: '#E5E5E5'
          }
        },
        axisLabel: {
          color: '#A3A3A3'
        }
      }
    ],
    series: [
      {
        name: 'Documents Processed',
        type: 'bar',
        data: [12450, 13200, 11890, 14120, 15670, 14930, 16200],
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#0066FF' },
            { offset: 1, color: '#003D99' }
          ])
        },
        barWidth: '40%'
      },
      {
        name: 'Errors',
        type: 'line',
        yAxisIndex: 1,
        data: [89, 76, 92, 68, 54, 61, 45],
        lineStyle: {
          color: '#EF4444',
          width: 3
        },
        itemStyle: {
          color: '#EF4444'
        }
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