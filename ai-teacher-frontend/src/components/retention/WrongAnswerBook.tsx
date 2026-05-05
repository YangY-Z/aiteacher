/**
 * 错题本组件
 * 展示学生的错题记录，支持按知识点筛选
 */

import React, { useState } from 'react';
import Tabs from 'antd/es/tabs';
import Tag from 'antd/es/tag';
import Empty from 'antd/es/empty';
import Button from 'antd/es/button';
import Progress from 'antd/es/progress';
import Modal from 'antd/es/modal';
import { 
  CheckCircleOutlined, 
  ExclamationCircleOutlined,
  ReloadOutlined,
  FilterOutlined 
} from '@ant-design/icons';
import type { TabsProps } from 'antd/es/tabs-props';
import './WrongAnswerBook.css';

export interface WrongAnswerRecord {
  id: number;
  questionId: string;
  kpId: string;
  kpName: string;
  questionContent: string;
  wrongAnswer: string;
  correctAnswer: string;
  errorType: string;
  errorAnalysis: string;
  wrongCount: number;
  correctCount: number;
  isMastered: boolean;
  firstWrongAt: string;
  lastWrongAt: string | null;
  lastCorrectAt: string | null;
}

export interface WrongAnswerBookData {
  studentId: number;
  records: WrongAnswerRecord[];
  pendingCount: number;
  masteredCount: number;
}

interface WrongAnswerBookProps {
  data: WrongAnswerBookData;
  onReview?: (record: WrongAnswerRecord) => void;
  onRefresh?: () => void;
}

/**
 * 错题本组件
 */
const WrongAnswerBook: React.FC<WrongAnswerBookProps> = ({
  data,
  onReview,
  onRefresh,
}) => {
  const [activeTab, setActiveTab] = useState('pending');
  const [selectedKp, setSelectedKp] = useState<string | null>(null);
  const [detailVisible, setDetailVisible] = useState(false);
  const [selectedRecord, setSelectedRecord] = useState<WrongAnswerRecord | null>(null);

  // 按知识点分组
  const groupedByKp = React.useMemo(() => {
    const groups: Record<string, WrongAnswerRecord[]> = {};
    data.records.forEach((record) => {
      if (!groups[record.kpId]) {
        groups[record.kpId] = [];
      }
      groups[record.kpId].push(record);
    });
    return groups;
  }, [data.records]);

  // 获取知识点列表
  const kpList = React.useMemo(() => {
    return Object.keys(groupedByKp).map((kpId) => ({
      id: kpId,
      name: groupedByKp[kpId][0]?.kpName || kpId,
      count: groupedByKp[kpId].length,
      pendingCount: groupedByKp[kpId].filter((r) => !r.isMastered).length,
    }));
  }, [groupedByKp]);

  // 筛选记录
  const filteredRecords = React.useMemo(() => {
    let records = data.records;
    
    if (activeTab === 'pending') {
      records = records.filter((r) => !r.isMastered);
    } else if (activeTab === 'mastered') {
      records = records.filter((r) => r.isMastered);
    }
    
    if (selectedKp) {
      records = records.filter((r) => r.kpId === selectedKp);
    }
    
    return records;
  }, [data.records, activeTab, selectedKp]);

  // 错误类型标签颜色
  const getErrorTypeTag = (type: string) => {
    const typeMap: Record<string, { color: string; text: string }> = {
      calculation: { color: 'orange', text: '计算错误' },
      concept: { color: 'red', text: '概念误解' },
      gap: { color: 'purple', text: '知识断层' },
      careless: { color: 'gold', text: '粗心大意' },
      procedure: { color: 'blue', text: '程序错误' },
    };
    const config = typeMap[type] || { color: 'default', text: type };
    return <Tag color={config.color}>{config.text}</Tag>;
  };

  // 显示详情
  const showDetail = (record: WrongAnswerRecord) => {
    setSelectedRecord(record);
    setDetailVisible(true);
  };

  // 渲染记录卡片
  const renderRecordCard = (record: WrongAnswerRecord) => (
    <div 
      key={record.id} 
      className={`wrong-record-card ${record.isMastered ? 'mastered' : ''}`}
      onClick={() => showDetail(record)}
    >
      <div className="record-header">
        <span className="kp-name">{record.kpName}</span>
        {getErrorTypeTag(record.errorType)}
      </div>
      
      <div className="record-content">
        {record.questionContent}
      </div>
      
      <div className="record-footer">
        <div className="answer-info">
          <span className="wrong">错误：{record.wrongAnswer}</span>
          <span className="correct">正确：{record.correctAnswer}</span>
        </div>
        <div className="mastery-info">
          {record.isMastered ? (
            <Tag icon={<CheckCircleOutlined />} color="success">
              已掌握
            </Tag>
          ) : (
            <Progress 
              percent={(record.correctCount / 3) * 100} 
              size="small" 
              showInfo={false}
              style={{ width: 60 }}
            />
          )}
        </div>
      </div>
    </div>
  );

  const tabItems: TabsProps['items'] = [
    {
      key: 'pending',
      label: (
        <span>
          <ExclamationCircleOutlined />
          待复习 ({data.pendingCount})
        </span>
      ),
    },
    {
      key: 'mastered',
      label: (
        <span>
          <CheckCircleOutlined />
          已掌握 ({data.masteredCount})
        </span>
      ),
    },
    {
      key: 'all',
      label: `全部 (${data.records.length})`,
    },
  ];

  return (
    <div className="wrong-answer-book">
      <div className="book-header">
        <h3>错题本</h3>
        <div className="header-actions">
          {onRefresh && (
            <Button type="text" icon={<ReloadOutlined />} onClick={onRefresh}>
              刷新
            </Button>
          )}
        </div>
      </div>

      {/* 知识点筛选 */}
      {kpList.length > 1 && (
        <div className="kp-filter">
          <span className="filter-label">
            <FilterOutlined /> 按知识点筛选：
          </span>
          <div className="kp-tags">
            <Tag
              color={selectedKp === null ? 'blue' : 'default'}
              onClick={() => setSelectedKp(null)}
              style={{ cursor: 'pointer' }}
            >
              全部
            </Tag>
            {kpList.map((kp) => (
              <Tag
                key={kp.id}
                color={selectedKp === kp.id ? 'blue' : 'default'}
                onClick={() => setSelectedKp(kp.id)}
                style={{ cursor: 'pointer' }}
              >
                {kp.name} ({kp.pendingCount}/{kp.count})
              </Tag>
            ))}
          </div>
        </div>
      )}

      {/* 标签页 */}
      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={tabItems}
      />

      {/* 记录列表 */}
      <div className="records-list">
        {filteredRecords.length > 0 ? (
          filteredRecords.map(renderRecordCard)
        ) : (
          <Empty
            description={activeTab === 'pending' ? '太棒了，没有待复习的错题！' : '暂无记录'}
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          />
        )}
      </div>

      {/* 详情弹窗 */}
      <Modal
        title="错题详情"
        open={detailVisible}
        onCancel={() => setDetailVisible(false)}
        footer={[
          <Button key="close" onClick={() => setDetailVisible(false)}>
            关闭
          </Button>,
          onReview && selectedRecord && !selectedRecord.isMastered && (
            <Button 
              key="review" 
              type="primary" 
              onClick={() => {
                onReview(selectedRecord);
                setDetailVisible(false);
              }}
            >
              开始复习
            </Button>
          ),
        ]}
      >
        {selectedRecord && (
          <div className="record-detail">
            <div className="detail-item">
              <span className="label">知识点：</span>
              <span>{selectedRecord.kpName}</span>
            </div>
            <div className="detail-item">
              <span className="label">题目：</span>
              <div className="question-text">{selectedRecord.questionContent}</div>
            </div>
            <div className="detail-item">
              <span className="label">你的答案：</span>
              <span className="wrong-answer">{selectedRecord.wrongAnswer}</span>
            </div>
            <div className="detail-item">
              <span className="label">正确答案：</span>
              <span className="correct-answer">{selectedRecord.correctAnswer}</span>
            </div>
            <div className="detail-item">
              <span className="label">错误类型：</span>
              {getErrorTypeTag(selectedRecord.errorType)}
            </div>
            {selectedRecord.errorAnalysis && (
              <div className="detail-item">
                <span className="label">错误分析：</span>
                <span>{selectedRecord.errorAnalysis}</span>
              </div>
            )}
            <div className="detail-item">
              <span className="label">掌握进度：</span>
              <span>
                {selectedRecord.isMastered 
                  ? '已掌握（连续正确3次）' 
                  : `还需正确${3 - selectedRecord.correctCount}次`}
              </span>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default WrongAnswerBook;
