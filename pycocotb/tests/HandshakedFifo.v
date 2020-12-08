/*

    Synchronous FIFO for handshaked interfaces

    .. aafig::
                 +-+-+-+-+-+
         input   | | | | | | output
       +-stream--> | | | | +-stream->
                 | | | | | |
                 +-+-+-+-+-+

    .. hwt-autodoc:: _example_HandshakedFifo
    
*/
module HandshakedFifo #(parameter  DATA_WIDTH = 8,
        parameter  DEPTH = 4,
        parameter  EXPORT_SIZE = 1
    )(input clk,
        input [DATA_WIDTH- 1:0] dataIn_data,
        output reg dataIn_rd,
        input dataIn_vld,
        output [DATA_WIDTH- 1:0] dataOut_data,
        input dataOut_rd,
        output dataOut_vld,
        input rst_n,
        output reg [3- 1:0] size
    );

    reg out_vld = 1'b0;
    reg out_vld_next;
    wire sig_fifo_clk;
    wire [7:0] sig_fifo_dataIn_data;
    reg sig_fifo_dataIn_en;
    wire sig_fifo_dataIn_wait;
    wire [7:0] sig_fifo_dataOut_data;
    reg sig_fifo_dataOut_en;
    wire sig_fifo_dataOut_wait;
    wire sig_fifo_rst_n;
    wire [1:0] sig_fifo_size;
    reg [3- 1:0] sizeTmp;
    fifo #(.DATA_WIDTH(8),
        .DEPTH(3),
        .EXPORT_SIZE(1),
        .EXPORT_SPACE(0)
        ) fifo_inst (.clk(sig_fifo_clk),
        .dataIn_data(sig_fifo_dataIn_data),
        .dataIn_en(sig_fifo_dataIn_en),
        .dataIn_wait(sig_fifo_dataIn_wait),
        .dataOut_data(sig_fifo_dataOut_data),
        .dataOut_en(sig_fifo_dataOut_en),
        .dataOut_wait(sig_fifo_dataOut_wait),
        .rst_n(sig_fifo_rst_n),
        .size(sig_fifo_size)
        );


    always @(sig_fifo_dataIn_wait) begin: assig_process_dataIn_rd
        dataIn_rd = ~sig_fifo_dataIn_wait;
    end

    assign dataOut_data = sig_fifo_dataOut_data;
    assign dataOut_vld = out_vld;
    always @(posedge clk) begin: assig_process_out_vld
        if(rst_n == 1'b0) begin
            out_vld <= 1'b0;
        end else begin
            out_vld <= out_vld_next;
        end
    end

    always @(dataOut_rd or out_vld or sig_fifo_dataOut_wait) begin: assig_process_out_vld_next
        if((dataOut_rd | (~out_vld))==1'b1) begin
            out_vld_next = ~sig_fifo_dataOut_wait;
        end else begin
            out_vld_next = out_vld;
        end
    end

    assign sig_fifo_clk = clk;
    assign sig_fifo_dataIn_data = dataIn_data;
    always @(dataIn_vld or sig_fifo_dataIn_wait) begin: assig_process_sig_fifo_dataIn_en
        sig_fifo_dataIn_en = dataIn_vld & (~sig_fifo_dataIn_wait);
    end

    always @(dataOut_rd or out_vld or sig_fifo_dataOut_wait) begin: assig_process_sig_fifo_dataOut_en
        sig_fifo_dataOut_en = (dataOut_rd | (~out_vld)) & (~sig_fifo_dataOut_wait);
    end

    assign sig_fifo_rst_n = rst_n;
    always @(out_vld or sig_fifo_size or sizeTmp) begin: assig_process_size
            reg [2:0] tmp_concat_0;
        tmp_concat_0 = {1'b0, sig_fifo_size};
        if((out_vld)==1'b1) begin
            size = sizeTmp + 3'(1);
        end else begin
            size = tmp_concat_0;
        end
    end

    always @(sig_fifo_size) begin: assig_process_sizeTmp
            reg [2:0] tmp_concat_1;
        tmp_concat_1 = {1'b0, sig_fifo_size};
        sizeTmp = tmp_concat_1;
    end

endmodule