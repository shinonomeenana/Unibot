import json

def events_master_helper(simplified_json_data):
    # 定义简化 JSON 中的索引与完整 JSON 字段的映射
    EVENT_FIELD_MAPPING = {
        0: "id",
        1: "eventType",
        2: "name",
        3: "assetbundleName",
        4: "bgmAssetbundleName",
        6: "startAt",
        8: "aggregateAt",
        9: "rankingAnnounceAt",
        10: "distributionStartAt",
        12: "closedAt",
        13: "virtualLiveId",
        14: "unit",
        15: "eventRankingRewardRanges"
    }

    # 定义奖励范围的索引映射
    EVENT_RANKING_REWARD_RANGES_MAPPING = {
        0: "fromRank",
        1: "toRank",
        2: "eventRankingRewards"
    }

    full_json_data = []

    for event in simplified_json_data:
        event_dict = {}
        for idx, value in enumerate(event):
            if idx in EVENT_FIELD_MAPPING:
                key = EVENT_FIELD_MAPPING[idx]
                if key == "eventRankingRewardRanges":
                    # 处理 eventRankingRewardRanges
                    event_ranking_reward_ranges = []
                    for reward_range in value:
                        reward_range_dict = {}
                        for idx_rr, val_rr in enumerate(reward_range):
                            if idx_rr in EVENT_RANKING_REWARD_RANGES_MAPPING:
                                key_rr = EVENT_RANKING_REWARD_RANGES_MAPPING[idx_rr]
                                if key_rr == "eventRankingRewards":
                                    # 处理 eventRankingRewards
                                    event_ranking_rewards = []
                                    for resource_box_ids in val_rr:
                                        for resource_box_id in resource_box_ids:
                                            event_ranking_rewards.append({"resourceBoxId": resource_box_id})
                                    reward_range_dict[key_rr] = event_ranking_rewards
                                else:
                                    reward_range_dict[key_rr] = val_rr
                        event_ranking_reward_ranges.append(reward_range_dict)
                    event_dict[key] = event_ranking_reward_ranges
                else:
                    event_dict[key] = value
        full_json_data.append(event_dict)
    return full_json_data

