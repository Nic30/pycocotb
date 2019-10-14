
module wire2 #(parameter  DATA_WIDTH = 2
    )(input [DATA_WIDTH- 1:0] inp,
        output [DATA_WIDTH- 1:0] outp
    );

    assign outp = inp;
endmodule
