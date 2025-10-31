import React, { useMemo } from 'react'
import EChartsReact from 'echarts-for-react'

export const ComplianceChart: React.FC = () => {
  const option = useMemo(() => ({
    title: {
      text: 'Compliance Scores',
      left: 'left',
      textStyle: {
        fontSize: 16,
        fontWeight: 600,
        color: '#171717'
      }
    },
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(255, 255, 255, 0.9)',
      borderColor: 'rgba(0, 0, 0, 0.1)',
      textStyle: {
        color: '#171717'
      },
      formatter: '{a} <br/>{b}: {c}% ({d}%)'
    },
    legend: {
      orient: 'vertical',
      right: '10%',
      top: 'center',
      textStyle: {
        color: '#A3A3A3',
        fontSize: 12
      }
    },
    series: [
      {
        name: 'Compliance',
        type: 'pie',
        radius: ['40%', '70%'],
        center: ['30%', '50%'],
        avoidLabelOverlap: false,
        label: {
          show: false,
          position: 'center'
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 20,
            fontWeight: 'bold',
            color: '#171717'
          }
        },
        labelLine: {
          show: false
        },
        data: [
          { 
            value: 98.5, 
            name: 'GDPR',
            itemStyle: {
              color: '#10B981'
            }
          },
          { 
            value: 94.2, 
            name: 'SOX',
            itemStyle: {
              color: '#3B82F6'
            }
          },
          { 
            value: 89.1, 
            name: 'HIPAA',
            itemStyle: {
              color: '#F59E0B'
            }
          },
          { 
            value: 97.3, 
            name: 'PCI DSS',
            itemStyle: {
              color: '#8B5CF6'
            }
          }
        ]
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