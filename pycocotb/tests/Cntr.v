
module Cntr #(parameter  DATA_WIDTH = 2
    )(input clk,
        input en,
        input rst,
        output [DATA_WIDTH- 1:0] val
    );

    reg [DATA_WIDTH- 1:0] counter = 2'b00;
    reg [DATA_WIDTH- 1:0] counter_next;
    always @(posedge clk) begin: assig_process_counter
        if(rst == 1'b1) begin
            counter <= 2'b00;
        end else begin
            counter <= counter_next;
        end
    end

    always @(counter or en) begin: assig_process_counter_next
        if((en)==1'b1) begin
            counter_next = counter + 2'(1);
        end else begin
            counter_next = counter;
        end
    end

    assign val = counter;
endmodule