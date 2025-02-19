// Copyright (C) 2022 Intel Corporation
// SPDX-License-Identifier: Apache-2.0
//

#include "common_test_utils/common_utils.hpp"
#include "snippets/two_inputs_and_outputs.hpp"
#include "subgraph_simple.hpp"

namespace ov {
namespace test {
namespace snippets {

std::string TwoInputsAndOutputs::getTestCaseName(testing::TestParamInfo<ov::test::snippets::TwoInputsAndOutputsParams> obj) {
    std::vector<ov::PartialShape> inputShapes;
    std::string targetDevice;
    size_t num_nodes, num_subgraphs;
    std::tie(inputShapes, num_nodes, num_subgraphs, targetDevice) = obj.param;

    std::ostringstream result;
    for (auto i = 0; i < inputShapes.size(); i++)
        result << "IS[" << i << "]=" << ov::test::utils::vec2str(inputShapes[i].get_shape()) << "_";
    result << "#N=" << num_nodes << "_";
    result << "#S=" << num_subgraphs << "_";
    result << "targetDevice=" << targetDevice;
    return result.str();
}

void TwoInputsAndOutputs::SetUp() {
    std::vector<ov::PartialShape> inputShape;
    std::tie(inputShape, ref_num_nodes, ref_num_subgraphs, targetDevice) = this->GetParam();
    init_input_shapes(static_partial_shapes_to_test_representation(inputShape));
    auto f = ov::test::snippets::TwoInputsAndOutputsFunction(inputShape);
    function = f.getOriginal();
}

void TwoInputsAndOutputsWithReversedOutputs::SetUp() {
    std::vector<ov::PartialShape> inputShape;
    std::tie(inputShape, ref_num_nodes, ref_num_subgraphs, targetDevice) = this->GetParam();
    init_input_shapes(static_partial_shapes_to_test_representation(inputShape));
    auto f = ov::test::snippets::TwoInputsAndOutputsWithReversedOutputsFunction(inputShape);
    function = f.getOriginal();
}

TEST_P(TwoInputsAndOutputs, CompareWithRefImpl) {
    run();
    validateNumSubgraphs();
}

TEST_P(TwoInputsAndOutputsWithReversedOutputs, CompareWithRefImpl) {
    run();
    validateNumSubgraphs();
}

} // namespace snippets
} // namespace test
} // namespace ov
