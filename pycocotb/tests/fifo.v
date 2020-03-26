/*

    Generic FIFO usually mapped to BRAM.

    :ivar ~.EXPORT_SIZE: parameter, if true "size" signal will be exported
    :ivar ~.size: optional signal with count of items stored in this fifo
    :ivar ~.EXPORT_SPACE: parameter, if true "space" signal is exported
    :ivar ~.space: optional signal with count of items which can be added to this fifo
    
    .. hwt-schematic:: _example_Fifo
    
*/
module fifo #(parameter  DATA_WIDTH = 8,
        parameter  DEPTH = 3,
        parameter  EXPORT_SIZE = 1,
        parameter  EXPORT_SPACE = 0
    )(input clk,
        input [DATA_WIDTH- 1:0] dataIn_data,
        input dataIn_en,
        output reg dataIn_wait,
        output reg [DATA_WIDTH- 1:0] dataOut_data,
        input dataOut_en,
        output reg dataOut_wait,
        input rst_n,
        output [2- 1:0] size
    );

    reg fifo_read;
    reg fifo_write;
    reg looped = 1'b0;
    reg looped_next;
    reg [DATA_WIDTH- 1:0] memory [DEPTH-1:0];
    reg [2- 1:0] rd_ptr = 0;
    reg [2- 1:0] rd_ptr_next;
    reg [2- 1:0] size_reg = 0;
    reg [2- 1:0] size_reg_next;
    reg [2- 1:0] wr_ptr = 0;
    reg [2- 1:0] wr_ptr_next;
    always @(looped or rd_ptr or wr_ptr) begin: assig_process_dataIn_wait
        if(wr_ptr == rd_ptr) begin
            if((looped)==1'b1) begin
                dataIn_wait = 1'b1;
                dataOut_wait = 1'b0;
            end else begin
                dataOut_wait = 1'b1;
                dataIn_wait = 1'b0;
            end
        end else begin
            dataIn_wait = 1'b0;
            dataOut_wait = 1'b0;
        end
    end

    always @(posedge clk) begin: assig_process_dataOut_data
        if((fifo_read)==1'b1) begin
            dataOut_data <= memory[rd_ptr];
        end
    end

    always @(dataOut_en or looped or rd_ptr or wr_ptr) begin: assig_process_fifo_read
        fifo_read = (dataOut_en == 1'b1) & ((looped == 1'b1) | (wr_ptr != rd_ptr));
    end

    always @(dataIn_en or looped or rd_ptr or wr_ptr) begin: assig_process_fifo_write
        fifo_write = (dataIn_en == 1'b1) & (((~looped) == 1'b1) | (wr_ptr != rd_ptr));
    end

    always @(dataIn_en or dataOut_en or rd_ptr or wr_ptr) begin: assig_process_looped_next
        if((dataIn_en == 1'b1) & (wr_ptr == 2'(DEPTH - 1))) begin
            looped_next = 1'b1;
        end else if((dataOut_en == 1'b1) & (rd_ptr == 2'(DEPTH - 1))) begin
            looped_next = 1'b0;
        end else begin
            looped_next = looped;
        end
    end

    always @(posedge clk) begin: assig_process_memory
        if((fifo_write)==1'b1) begin
            memory[wr_ptr] <= dataIn_data;
        end
    end

    always @(fifo_read or rd_ptr) begin: assig_process_rd_ptr_next
        if((fifo_read)==1'b1) begin
            if(rd_ptr == 2'(DEPTH - 1)) begin
                rd_ptr_next = 0;
            end else begin
                rd_ptr_next = rd_ptr + 2'(1);
            end
        end else begin
            rd_ptr_next = rd_ptr;
        end
    end

    assign size = size_reg;
    always @(fifo_read or fifo_write or size_reg) begin: assig_process_size_reg_next
        if((fifo_read)==1'b1) begin
            if((~fifo_write)==1'b1) begin
                size_reg_next = size_reg - 2'(1);
            end else begin
                size_reg_next = size_reg;
            end
        end else if((fifo_write)==1'b1) begin
            size_reg_next = size_reg + 2'(1);
        end else begin
            size_reg_next = size_reg;
        end
    end

    always @(posedge clk) begin: assig_process_wr_ptr
        if(rst_n == 1'b0) begin
            wr_ptr <= 0;
            size_reg <= 0;
            rd_ptr <= 0;
            looped <= 1'b0;
        end else begin
            wr_ptr <= wr_ptr_next;
            size_reg <= size_reg_next;
            rd_ptr <= rd_ptr_next;
            looped <= looped_next;
        end
    end

    always @(fifo_write or wr_ptr) begin: assig_process_wr_ptr_next
        if((fifo_write)==1'b1) begin
            if(wr_ptr == 2'(DEPTH - 1)) begin
                wr_ptr_next = 0;
            end else begin
                wr_ptr_next = wr_ptr + 2'(1);
            end
        end else begin
            wr_ptr_next = wr_ptr;
        end
    end

endmodule