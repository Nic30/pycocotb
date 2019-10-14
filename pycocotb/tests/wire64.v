
module wire64 #(parameter  DATA_WIDTH = 64
    )(input [DATA_WIDTH- 1:0] inp,
        output [DATA_WIDTH- 1:0] outp
    );

    assign outp = inp;
endmodule
