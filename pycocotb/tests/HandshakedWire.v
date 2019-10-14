module HandshakedWire #(
        parameter DATA_WIDTH = 8
    )(
        input clk,
        input [DATA_WIDTH- 1:0] dataIn_data,
        output dataIn_rd,
        input dataIn_vld,

        output [DATA_WIDTH- 1:0] dataOut_data,
        input dataOut_rd,
        output dataOut_vld,

        input rst_n
    );

    assign dataOut_data = dataIn_data;
    assign dataIn_rd = dataOut_rd;
    assign dataOut_vld = dataIn_vld;

endmodule